/**
 * Kafka Middleware para Protheus
 * 
 * Middleware HTTP que recebe requisições REST do Protheus
 * e envia para Kafka usando protocolo binário nativo
 * 
 * @author Fernando Vernier
 * @version 1.0
 * @see https://github.com/ftvernier/erp-solutions/tree/main/kafka
 */

require('dotenv').config();

const express = require('express');
const { Kafka, logLevel } = require('kafkajs');
const morgan = require('morgan');
const helmet = require('helmet');

// Configurações
const PORT = process.env.PORT || 8080;
const KAFKA_BROKERS = process.env.KAFKA_BROKERS || 
    'kafka-broker-1:9092,kafka-broker-2:9092,kafka-broker-3:9094';

// Inicializa Express
const app = express();

// Middlewares
app.use(helmet()); // Segurança
app.use(express.json({ limit: '10mb' })); // Parse JSON
app.use(morgan('combined')); // Logs HTTP

// Configuração do Kafka
const kafka = new Kafka({
    clientId: 'protheus-middleware',
    brokers: KAFKA_BROKERS.split(','),
    retry: {
        initialRetryTime: 100,
        retries: 8,
        maxRetryTime: 30000,
        multiplier: 2
    },
    connectionTimeout: 10000,
    requestTimeout: 30000,
    logLevel: logLevel.INFO
});

// Cria producer
const producer = kafka.producer({
    allowAutoTopicCreation: false,
    transactionTimeout: 30000,
    maxInFlightRequests: 5,
    idempotent: true,
    compression: 1 // GZIP
});

// Variável de controle de conexão
let isConnected = false;

// Conecta ao Kafka
async function connectKafka() {
    if (isConnected) return true;
    
    try {
        console.log('[KAFKA] Conectando aos brokers...');
        console.log('[KAFKA] Brokers:', KAFKA_BROKERS);
        
        await producer.connect();
        isConnected = true;
        
        console.log('[KAFKA] ✅ Conectado com sucesso!');
        return true;
    } catch (error) {
        console.error('[KAFKA] ❌ Erro ao conectar:', error.message);
        isConnected = false;
        return false;
    }
}

// Reconecta se desconectar
producer.on('producer.disconnect', () => {
    console.log('[KAFKA] ⚠️  Desconectado! Tentando reconectar...');
    isConnected = false;
    setTimeout(connectKafka, 5000);
});

// Health Check
app.get('/health', (req, res) => {
    res.json({
        status: isConnected ? 'healthy' : 'unhealthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        kafka: {
            connected: isConnected,
            brokers: KAFKA_BROKERS.split(',')
        }
    });
});

// Lista tópicos (compatibilidade com código AdvPL)
app.get('/topics', async (req, res) => {
    try {
        const admin = kafka.admin();
        await admin.connect();
        
        const topics = await admin.listTopics();
        await admin.disconnect();
        
        res.json(topics);
    } catch (error) {
        console.error('[TOPICS] Erro:', error.message);
        res.status(500).json({ 
            error: error.message 
        });
    }
});

// Endpoint principal - POST para tópico
app.post('/topics/:topic', async (req, res) => {
    const startTime = Date.now();
    const { topic } = req.params;
    const { key, data } = req.body;
    
    console.log(`[POST] Tópico: ${topic}, Key: ${key}`);
    
    try {
        // Verifica se está conectado
        if (!isConnected) {
            const connected = await connectKafka();
            if (!connected) {
                throw new Error('Não foi possível conectar ao Kafka');
            }
        }
        
        // Prepara mensagem
        const message = {
            key: key || null,
            value: JSON.stringify(data),
            timestamp: Date.now().toString()
        };
        
        // Envia para Kafka
        const result = await producer.send({
            topic: topic,
            messages: [message],
            timeout: 30000
        });
        
        const duration = Date.now() - startTime;
        
        console.log(`[POST] ✅ Sucesso em ${duration}ms`);
        
        // Log detalhado do que o Kafka retornou
        console.log(`[POST] Resultado completo:`, JSON.stringify(result, null, 2));
        
        // Resposta compatível com Kafka REST Proxy
        res.json({
            offsets: result.map(r => {
                // Converter offset para string, tratando BigInt
                let offsetStr = '0';
                // O Kafka retorna como 'baseOffset', não 'offset'
                if (r.baseOffset !== undefined && r.baseOffset !== null) {
                    offsetStr = String(r.baseOffset);
                } else if (r.offset !== undefined && r.offset !== null) {
                    offsetStr = String(r.offset);
                }
                
                console.log(`[POST] Offset: ${offsetStr}, Partition: ${r.partition}`);
                
                return {
                    offset: offsetStr,
                    partition: r.partition || 0,
                    error_code: null,
                    error: null
                };
            }),
            key_schema_id: null,
            value_schema_id: null
        });
        
    } catch (error) {
        const duration = Date.now() - startTime;
        
        console.error(`[POST] ❌ Erro em ${duration}ms:`, error.message);
        
        res.status(500).json({
            error_code: 500,
            error: error.message,
            message: 'Falha ao enviar mensagem para Kafka'
        });
    }
});

// Endpoint de métricas
app.get('/metrics', async (req, res) => {
    try {
        const admin = kafka.admin();
        await admin.connect();
        
        const cluster = await admin.describeCluster();
        await admin.disconnect();
        
        res.json({
            middleware: {
                uptime: process.uptime(),
                memory: process.memoryUsage(),
                connected: isConnected
            },
            kafka: {
                clusterId: cluster.clusterId,
                brokers: cluster.brokers.map(b => ({
                    nodeId: b.nodeId,
                    host: b.host,
                    port: b.port
                })),
                controller: cluster.controller
            }
        });
    } catch (error) {
        res.status(500).json({ 
            error: error.message 
        });
    }
});

// Endpoint para criar tópico
app.post('/admin/topics', async (req, res) => {
    const { topic, partitions = 3, replicationFactor = 2 } = req.body;
    
    try {
        const admin = kafka.admin();
        await admin.connect();
        
        await admin.createTopics({
            topics: [{
                topic: topic,
                numPartitions: partitions,
                replicationFactor: replicationFactor
            }]
        });
        
        await admin.disconnect();
        
        console.log(`[ADMIN] Tópico '${topic}' criado com sucesso`);
        
        res.json({
            success: true,
            message: `Tópico '${topic}' criado com sucesso`,
            config: {
                topic,
                partitions,
                replicationFactor
            }
        });
    } catch (error) {
        console.error('[ADMIN] Erro ao criar tópico:', error.message);
        res.status(500).json({ 
            error: error.message 
        });
    }
});

// Tratamento de erros
app.use((err, req, res, next) => {
    console.error('[ERROR]', err);
    res.status(500).json({
        error: err.message,
        timestamp: new Date().toISOString()
    });
});

// Inicializa servidor
async function start() {
    try {
        console.log('');
        console.log('🚀 Kafka Middleware para Protheus');
        console.log('📦 Versão: 1.0.0');
        console.log('👤 Autor: Fernando Vernier');
        console.log('');
        
        // Conecta ao Kafka primeiro
        await connectKafka();
        
        // Inicia servidor HTTP
        app.listen(PORT, () => {
            console.log('');
            console.log('✅ Servidor iniciado com sucesso!');
            console.log(`📡 HTTP Server rodando em: http://localhost:${PORT}`);
            console.log(`🔗 Kafka Brokers: ${KAFKA_BROKERS}`);
            console.log('');
            console.log('📋 Endpoints disponíveis:');
            console.log(`   POST   http://localhost:${PORT}/topics/:topic`);
            console.log(`   GET    http://localhost:${PORT}/topics`);
            console.log(`   GET    http://localhost:${PORT}/health`);
            console.log(`   GET    http://localhost:${PORT}/metrics`);
            console.log(`   POST   http://localhost:${PORT}/admin/topics`);
            console.log('');
            console.log('🎯 Pronto para receber requisições do Protheus!');
            console.log('');
        });
        
    } catch (error) {
        console.error('❌ Erro ao iniciar servidor:', error);
        process.exit(1);
    }
}

// Graceful shutdown
process.on('SIGTERM', async () => {
    console.log('[SHUTDOWN] Recebido SIGTERM, desconectando...');
    await producer.disconnect();
    process.exit(0);
});

process.on('SIGINT', async () => {
    console.log('[SHUTDOWN] Recebido SIGINT, desconectando...');
    await producer.disconnect();
    process.exit(0);
});

// Inicia aplicação
start();
