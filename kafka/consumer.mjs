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
          processInvoiceIssued(event.data);
          break;
        default:
          console.log(`⚠️  Tipo de evento desconhecido: ${event.event_type}`);
      }
      
      console.log('='.repeat(80) + '\n');
    },
  });
};

// Processa evento de NF emitida
const processInvoiceIssued = (data) => {
  console.log('\n🧾 NOTA FISCAL EMITIDA');
  console.log(`   Número: ${data.numero_nf} | Série: ${data.serie}`);
  console.log(`   Filial: ${data.filial}`);
  console.log(`   Emissão: ${data.emissao}`);
  
  if (data.chave_nfe) {
    console.log(`   Chave NFe: ${data.chave_nfe}`);
  }
  
  console.log('\n👤 CLIENTE');
  console.log(`   ${data.cliente.codigo}/${data.cliente.loja} - ${data.cliente.nome}`);
  console.log(`   CNPJ: ${data.cliente.cnpj}`);
  console.log(`   ${data.cliente.municipio}/${data.cliente.uf}`);
  
  console.log('\n💰 VALORES');
  console.log(`   Total Produtos: R$ ${data.valores.total_produtos.toFixed(2)}`);
  console.log(`   Total NF: R$ ${data.valores.total_nf.toFixed(2)}`);
  console.log(`   ICMS: R$ ${data.valores.icms.toFixed(2)}`);
  console.log(`   IPI: R$ ${data.valores.ipi.toFixed(2)}`);
  
  if (data.valores.desconto > 0) {
    console.log(`   Desconto: R$ ${data.valores.desconto.toFixed(2)}`);
  }
  
  console.log(`\n📦 ITENS (${data.total_itens})`);
  data.itens.forEach((item, index) => {
    console.log(`   ${index + 1}. ${item.produto} - ${item.descricao}`);
    console.log(`      Qtd: ${item.quantidade} | Unit: R$ ${item.valor_unitario.toFixed(2)} | Total: R$ ${item.valor_total.toFixed(2)}`);
  });
  
  if (data.transportadora && data.transportadora.nome) {
    console.log(`\n🚚 TRANSPORTADORA`);
    console.log(`   ${data.transportadora.codigo} - ${data.transportadora.nome}`);
  }
  
  // Aqui você pode adicionar suas regras de negócio
  // Exemplos:
  // - Enviar notificação para logística
  // - Atualizar sistema de WMS
  // - Disparar integração com marketplace
  // - Registrar em analytics/BI
  // - Enviar email para cliente
  
  console.log('\n✅ Evento processado com sucesso!');
};

// Tratamento de erros
const errorTypes = ['unhandledRejection', 'uncaughtException'];
const signalTraps = ['SIGTERM', 'SIGINT', 'SIGUSR2'];

errorTypes.forEach(type => {
  process.on(type, async (error) => {
    try {
      console.error(`❌ ${type}: ${error.message}`);
      await consumer.disconnect();
      process.exit(0);
    } catch (_) {
      process.exit(1);
    }
  });
});

signalTraps.forEach(type => {
  process.once(type, async () => {
    try {
      console.log(`\n🛑 Recebido sinal ${type}, encerrando consumer...`);
      await consumer.disconnect();
      process.exit(0);
    } catch (_) {
      process.exit(1);
    }
  });
});

// Inicia o consumer
console.log('🚀 Iniciando Protheus Consumer Example...');
console.log(`📡 Kafka Brokers: ${process.env.KAFKA_BROKERS || 'kafka:9092'}`);
console.log(`👥 Group ID: ${process.env.KAFKA_GROUP_ID || 'protheus-consumer-group'}`);
console.log(`📋 Tópicos: ${topics.join(', ')}`);
console.log('-'.repeat(80));

run().catch(console.error);
