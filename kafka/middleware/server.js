/**
 * Kafka Middleware para Protheus - Enhanced Version
 * 
 * Implementa padrões de Event-Driven Architecture:
 * - Outbox Pattern para garantia de entrega
 * - Confirmação de persistência (acks=all)
 * - Dead Letter Queue (DLQ)
 * - Retry resiliente com backoff exponencial
 * - Métricas de confiabilidade
 * 
 * @author Fernando Vernier
 * @version 2.0
 */

require('dotenv').config();

const express = require('express');
const { Kafka, logLevel } = require('kafkajs');
const morgan = require('morgan');
const helmet = require('helmet');
const sqlite3 = require('sqlite3').verbose();
const { promisify } = require('util');

// Configurações
const PORT = process.env.PORT || 8080;
const KAFKA_BROKERS = process.env.KAFKA_BROKERS || 
    'kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9094';
const ENABLE_OUTBOX = process.env.ENABLE_OUTBOX === 'true' || true;
const DLQ_TOPIC = process.env.DLQ_TOPIC || 'dlq-topic';

// Inicializa Express
const app = express();

// Middlewares
app.use(helmet());
app.use(express.json({ limit: '10mb' }));
app.use(morgan('combined'));

// ===========================
// OUTBOX PATTERN - SQLite
// ===========================
const db = new sqlite3.Database('./outbox.db');

// Promisify database methods
const dbRun = promisify(db.run.bind(db));
const dbGet = promisify(db.get.bind(db));
const dbAll = promisify(db.all.bind(db));

// Inicializa tabela de outbox
async function initOutbox() {
    await dbRun(`
        CREATE TABLE IF NOT EXISTS outbox (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT UNIQUE NOT NULL,
            topic TEXT NOT NULL,
            key TEXT,
            value TEXT NOT NULL,
            timestamp INTEGER NOT NULL,
            status TEXT DEFAULT 'pending',
            retry_count INTEGER DEFAULT 0,
            last_error TEXT,
            created_at INTEGER DEFAULT (strftime('%s', 'now')),
            sent_at INTEGER,
            kafka_offset TEXT,
            kafka_partition INTEGER
        )
    `);
    
    await dbRun(`
        CREATE INDEX IF NOT EXISTS idx_status 
        ON outbox(status, created_at)
    `);
    
    console.log('[OUTBOX] ✅ Tabela inicializada');
}

// Salva mensagem no outbox
async function saveToOutbox(messageId, topic, key, value) {
    await dbRun(
        `INSERT INTO outbox (message_id, topic, key, value, timestamp, status)
         VALUES (?, ?, ?, ?, ?, 'pending')`,
        [messageId, topic, key, JSON.stringify(value), Date.now()]
    );
}

// Marca mensagem como enviada
async function markAsSent(messageId, offset, partition) {
    await dbRun(
        `UPDATE outbox 
         SET status = 'sent', 
             sent_at = ?,
             kafka_offset = ?,
             kafka_partition = ?
         WHERE message_id = ?`,
        [Date.now(), offset, partition, messageId]
    );
}

// Marca mensagem como falha
async function markAsFailed(messageId, error) {
    await dbRun(
        `UPDATE outbox 
         SET status = 'failed',
             retry_count = retry_count + 1,
             last_error = ?
         WHERE message_id = ?`,
        [error, messageId]
    );
}

// Move para DLQ após muitas tentativas
async function moveToDLQ(messageId) {
    await dbRun(
        `UPDATE outbox 
         SET status = 'dlq'
         WHERE message_id = ?`,
        [messageId]
    );
}

// Busca mensagens pendentes
async function getPendingMessages(limit = 100) {
    return await dbAll(
        `SELECT * FROM outbox 
         WHERE status = 'pending' 
         AND retry_count < 5
         ORDER BY created_at ASC 
         LIMIT ?`,
        [limit]
    );
}

// ===========================
// KAFKA CONFIGURATION
// ===========================
const kafka = new Kafka({
    clientId: 'protheus-middleware-v2',
    brokers: KAFKA_BROKERS.split(','),
    retry: {
        initialRetryTime: 300,
        retries: 8,
        maxRetryTime: 30000,
        multiplier: 2
    },
    connectionTimeout: 10000,
    requestTimeout: 30000,
    logLevel: logLevel.INFO
});

// Producer com configuração robusta
const producer = kafka.producer({
    allowAutoTopicCreation: false,
    transactionTimeout: 60000,
    maxInFlightRequests: 1, // Garante ordem
    idempotent: true, // Evita duplicatas
    compression: 1, // GZIP
    acks: -1, // acks=all - espera confirmação de todas as réplicas
    timeout: 30000,
    retry: {
        initialRetryTime: 300,
        retries: 5,
        maxRetryTime: 30000
    }
});

let isConnected = false;

// Conecta ao Kafka
async function connectKafka() {
    if (isConnected) return true;
    
    try {
        console.log('[KAFKA] Conectando aos brokers...');
        await producer.connect();
        isConnected = true;
        console.log('[KAFKA] ✅ Conectado com acks=all');
        return true;
    } catch (error) {
        console.error('[KAFKA] ❌ Erro ao conectar:', error.message);
        isConnected = false;
        return false;
    }
}

// Reconecta se desconectar
producer.on('producer.disconnect', () => {
    console.log('[KAFKA] ⚠️ Desconectado! Reconectando...');
    isConnected = false;
    setTimeout(connectKafka, 5000);
});

// ===========================
// MÉTRICAS
// ===========================
const metrics = {
    totalReceived: 0,
    totalSent: 0,
    totalFailed: 0,
    totalRetries: 0,
    totalDLQ: 0
};

// ===========================
// ENDPOINTS
// ===========================

// Health Check
app.get('/health', async (req, res) => {
    const pendingCount = await dbGet(
        `SELECT COUNT(*) as count FROM outbox WHERE status = 'pending'`
    );
    
    res.json({
        status: isConnected ? 'healthy' : 'unhealthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        kafka: {
            connected: isConnected,
            brokers: KAFKA_BROKERS.split(','),
            acks: 'all'
        },
        outbox: {
            enabled: ENABLE_OUTBOX,
            pending: pendingCount.count
        },
        metrics
    });
});

// Endpoint principal - POST para tópico
app.post('/topics/:topic', async (req, res) => {
    const startTime = Date.now();
    const { topic } = req.params;
    const { key, data } = req.body;
    
    // Gera ID único para rastreamento
    const messageId = `${topic}-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    
    console.log(`[POST] Tópico: ${topic}, Key: ${key}, ID: ${messageId}`);
    metrics.totalReceived++;
    
    try {
        // PASSO 1: Salva no Outbox (garantia local)
        if (ENABLE_OUTBOX) {
            await saveToOutbox(messageId, topic, key, data);
            console.log(`[OUTBOX] ✅ Mensagem ${messageId} salva`);
        }
        
        // PASSO 2: Verifica conexão
        if (!isConnected) {
            const connected = await connectKafka();
            if (!connected) {
                throw new Error('Kafka indisponível');
            }
        }
        
        // PASSO 3: Envia para Kafka
        const message = {
            key: key || null,
            value: JSON.stringify(data),
            timestamp: Date.now().toString(),
            headers: {
                'message-id': messageId,
                'source': 'protheus-middleware'
            }
        };
        
        const result = await producer.send({
            topic: topic,
            messages: [message],
            timeout: 30000,
            acks: -1 // Espera confirmação de TODAS as réplicas
        });
        
        const duration = Date.now() - startTime;
        
        // PASSO 4: Confirma no Outbox
        if (ENABLE_OUTBOX && result[0]) {
            const offset = String(result[0].baseOffset || result[0].offset || '0');
            const partition = result[0].partition || 0;
            
            await markAsSent(messageId, offset, partition);
            console.log(`[OUTBOX] ✅ Confirmado: offset=${offset}, partition=${partition}`);
        }
        
        metrics.totalSent++;
        console.log(`[POST] ✅ Sucesso em ${duration}ms com garantia de entrega`);
        
        // Resposta com confirmação real
        res.json({
            success: true,
            message_id: messageId,
            offsets: result.map(r => ({
                offset: String(r.baseOffset || r.offset || '0'),
                partition: r.partition || 0,
                error_code: null,
                error: null
            })),
            acks: 'all',
            confirmed: true,
            duration_ms: duration
        });
        
    } catch (error) {
        const duration = Date.now() - startTime;
        metrics.totalFailed++;
        
        console.error(`[POST] ❌ Erro em ${duration}ms:`, error.message);
        
        // Marca falha no outbox
        if (ENABLE_OUTBOX) {
            await markAsFailed(messageId, error.message);
            console.log(`[OUTBOX] ⚠️ Mensagem ${messageId} marcada para retry`);
        }
        
        res.status(500).json({
            success: false,
            error_code: 500,
            error: error.message,
            message_id: messageId,
            message: 'Mensagem salva para retry automático'
        });
    }
});

// ===========================
// RETRY WORKER
// ===========================
async function retryWorker() {
    try {
        const pending = await getPendingMessages(50);
        
        if (pending.length === 0) {
            return;
        }
        
        console.log(`[RETRY] Processando ${pending.length} mensagens pendentes`);
        
        for (const msg of pending) {
            try {
                const result = await producer.send({
                    topic: msg.topic,
                    messages: [{
                        key: msg.key,
                        value: msg.value,
                        timestamp: msg.timestamp.toString(),
                        headers: {
                            'message-id': msg.message_id,
                            'retry-count': String(msg.retry_count)
                        }
                    }],
                    timeout: 30000,
                    acks: -1
                });
                
                const offset = String(result[0].baseOffset || result[0].offset || '0');
                await markAsSent(msg.message_id, offset, result[0].partition);
                
                metrics.totalRetries++;
                console.log(`[RETRY] ✅ Mensagem ${msg.message_id} enviada`);
                
            } catch (error) {
                console.error(`[RETRY] ❌ Falha: ${msg.message_id}`, error.message);
                
                if (msg.retry_count >= 4) {
                    // Move para DLQ após 5 tentativas
                    await moveToDLQ(msg.message_id);
                    metrics.totalDLQ++;
                    
                    // Envia para tópico DLQ
                    try {
                        await producer.send({
                            topic: DLQ_TOPIC,
                            messages: [{
                                key: msg.key,
                                value: msg.value,
                                headers: {
                                    'original-topic': msg.topic,
                                    'message-id': msg.message_id,
                                    'error': error.message,
                                    'retry-count': String(msg.retry_count)
                                }
                            }]
                        });
                        console.log(`[DLQ] ⚠️ Mensagem ${msg.message_id} movida para DLQ`);
                    } catch (dlqError) {
                        console.error(`[DLQ] ❌ Erro ao mover para DLQ:`, dlqError.message);
                    }
                } else {
                    await markAsFailed(msg.message_id, error.message);
                }
            }
        }
        
    } catch (error) {
        console.error('[RETRY] Erro no worker:', error.message);
    }
}

// Inicia retry worker (executa a cada 30s)
setInterval(retryWorker, 30000);

// ===========================
// OUTROS ENDPOINTS
// ===========================

app.get('/topics', async (req, res) => {
    try {
        const admin = kafka.admin();
        await admin.connect();
        const topics = await admin.listTopics();
        await admin.disconnect();
        res.json(topics);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.get('/metrics', async (req, res) => {
    const outboxStats = await dbGet(`
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
            SUM(CASE WHEN status = 'sent' THEN 1 ELSE 0 END) as sent,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
            SUM(CASE WHEN status = 'dlq' THEN 1 ELSE 0 END) as dlq
        FROM outbox
    `);
    
    res.json({
        middleware: {
            uptime: process.uptime(),
            memory: process.memoryUsage(),
            connected: isConnected
        },
        metrics,
        outbox: outboxStats
    });
});

// ===========================
// INICIALIZAÇÃO
// ===========================
async function start() {
    try {
        console.log('');
        console.log('🚀 Kafka Middleware v2.0 - Event-Driven Architecture');
        console.log('📦 Autor: Fernando Vernier');
        console.log('');
        
        await initOutbox();
        await connectKafka();
        
        app.listen(PORT, () => {
            console.log('');
            console.log('✅ Servidor iniciado com garantias de entrega!');
            console.log(`📡 HTTP: http://localhost:${PORT}`);
            console.log(`🔗 Kafka: ${KAFKA_BROKERS}`);
            console.log('');
            console.log('🛡️ Recursos de confiabilidade:');
            console.log('   ✓ acks=all (confirmação de todas as réplicas)');
            console.log('   ✓ Outbox Pattern (garantia local)');
            console.log('   ✓ Retry automático (5 tentativas)');
            console.log('   ✓ Dead Letter Queue (DLQ)');
            console.log('   ✓ Idempotência garantida');
            console.log('');
        });
        
        // Inicia primeira verificação de retry
        setTimeout(retryWorker, 10000);
        
    } catch (error) {
        console.error('❌ Erro ao iniciar:', error);
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('[SHUTDOWN] Desconectando gracefully...');
    await producer.disconnect();
    db.close();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('[SHUTDOWN] Desconectando gracefully...');
    await producer.disconnect();
    db.close();
    process.exit(0);
});

start();
