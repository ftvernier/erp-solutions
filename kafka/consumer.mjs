import { Kafka } from 'kafkajs';

const kafka = new Kafka({
  clientId: 'protheus-consumer-example',
  brokers: [process.env.KAFKA_BROKERS || 'kafka:9092']
});

const consumer = kafka.consumer({ 
  groupId: process.env.KAFKA_GROUP_ID || 'protheus-consumer-group' 
});

const topics = (process.env.KAFKA_TOPICS || 'protheus.invoices.issued').split(',');

const run = async () => {
  // Conecta o consumer
  await consumer.connect();
  console.log('✅ Consumer conectado ao Kafka');

  // Inscreve nos tópicos
  for (const topic of topics) {
    await consumer.subscribe({ topic: topic.trim(), fromBeginning: true });
    console.log(`📥 Inscrito no tópico: ${topic.trim()}`);
  }

  // Processa mensagens
  await consumer.run({
    eachMessage: async ({ topic, partition, message }) => {
      const event = JSON.parse(message.value.toString());
      
      console.log('\n' + '='.repeat(80));
      console.log('📨 NOVO EVENTO RECEBIDO');
      console.log('='.repeat(80));
      console.log(`🏷️  Tópico: ${topic}`);
      console.log(`🔑 Event ID: ${event.event_id}`);
      console.log(`📋 Tipo: ${event.event_type}`);
      console.log(`⏰ Timestamp: ${event.timestamp}`);
      console.log(`🔗 Source: ${event.source}`);
      console.log('-'.repeat(80));
      
      // Processa baseado no tipo de evento
      switch (event.event_type) {
        case 'invoice_issued':
          processInvoiceIssue
