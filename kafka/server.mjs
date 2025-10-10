import express from 'express';
import { Kafka } from 'kafkajs';
import winston from 'winston';

// Configuração de logs
const logger = winston.createLogger({
  level: 'info',
  format: winston.format.combine(
    winston.format.timestamp(),
    winston.format.json()
  ),
  transports: [
    new winston.transports.Console({
      format: winston.format.simple()
    }),
    new winston.transports.File({ filename: 'error.log', level: 'error' }),
    new winston.transports.File({ filename: 'combined.log' })
  ]
});

// Configuração do Express
const app = express();
app.use(express.json({ limit: '10mb' }));

// Configuração do Kafka
const kafka = new Kafka({
  clientId: 'protheus-publisher',
  brokers: [process.env.KAFKA_BROKERS || 'kafka:9092'],
  retry: {
    initialRetryTime: 100,
    retries: 8
  }
});

const producer = kafka.producer({
  allowAutoTopicCreation: true,
  transactionTimeout: 30000
});

// Conecta ao Kafka
let isKafkaReady = false;

const connectKafka = async () => {
  try {
    await producer.connect();
    isKafkaReady = true;
    logger.info('✅ Conectado ao Kafka com sucesso!');
  } catch (error) {
    isKafkaReady = false;
    logger.error('❌ Erro ao conectar no Kafka:', error.message);
    // Tenta reconectar após 5 segundos
    setTimeout(connectKafka, 5000);
  }
};

connectKafka();

// Health check
app.get('/health', (req, res) => {
  res.json({
    status: 'online',
    kafka: isKafkaReady ? 'connected' : 'disconnected',
    timestamp: new Date().toISOString()
  });
});

// Endpoint principal - Publica evento no Kafka
app.post('/publish', async (req, res) => {
  const startTime = Date.now();
  
  try {
    const { event_id, event_type, topic, timestamp, source, data } = req.body;

    // Validações
    if (!event_id || !event_type || !topic || !data) {
      logger.warn('⚠️ Requisição inválida - campos obrigatórios ausentes');
      return res.status(400).json({
        success: false,
        error: 'Campos obrigatórios: event_id, event_type, topic, data'
      });
    }

    if (!isKafkaReady) {
      logger.error('❌ Kafka não está conectado');
      return res.status(503).json({
        success: false,
        error: 'Kafka não disponível'
      });
    }

    // Monta mensagem para o Kafka
    const message = {
      key: event_id,
      value: JSON.stringify({
        event_id,
        event_type,
        timestamp: timestamp || new Date().toISOString(),
        source: source || 'protheus_erp',
        data
      }),
      headers: {
        'event-type': event_type,
        'source': source || 'protheus_erp',
        'content-type': 'application/json'
      }
    };

    // Envia para o Kafka
    await producer.send({
      topic: topic,
      messages: [message]
    });

    const duration = Date.now() - startTime;

    logger.info(`✅ Evento publicado com sucesso`, {
      event_id,
      event_type,
      topic,
      duration_ms: duration
    });

    res.json({
      success: true,
      event_id,
      topic,
      duration_ms: duration
    });

  } catch (error) {
    const duration = Date.now() - startTime;
    
    logger.error('❌ Erro ao publicar evento:', {
      error: error.message,
      stack: error.stack,
      duration_ms: duration
    });

    res.status(500).json({
      success: false,
      error: 'Erro ao publicar evento no Kafka',
      details: error.message
    });
  }
});

// Endpoint para listar tópicos
app.get('/topics', async (req, res) => {
  try {
    const admin = kafka.admin();
    await admin.connect();
    const topics = await admin.listTopics();
    await admin.disconnect();

    res.json({
      success: true,
      topics
    });
  } catch (error) {
    logger.error('❌ Erro ao listar tópicos:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Graceful shutdown
const shutdown = async () => {
  logger.info('🛑 Encerrando aplicação...');
  try {
    await producer.disconnect();
    logger.info('✅ Kafka desconectado');
  } catch (error) {
    logger.error('❌ Erro ao desconectar Kafka:', error.message);
  }
  process.exit(0);
};

process.on('SIGTERM', shutdown);
process.on('SIGINT', shutdown);

// Inicia servidor
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
  logger.info(`🚀 Middleware rodando na porta ${PORT}`);
  logger.info(`📊 Health check: http://localhost:${PORT}/health`);
  logger.info(`📝 Publish endpoint: http://localhost:${PORT}/publish`);
});
