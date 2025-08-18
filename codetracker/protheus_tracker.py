#!/usr/bin/env python3
"""
Instrumentador Automático para Protheus Code Tracker
Adiciona automaticamente chamadas U_TrackExecution() em todos os códigos AdvPL

Autor: Fernando Vernier
Data: 01/08/2025
E-mail: fernando.vernier@hotmail.com
"""

import os
import re
import shutil
from pathlib import Path

class ProtheusInstrumenter:
    def __init__(self, project_path, backup_path=None):
        self.project_path = Path(project_path)
        self.backup_path = Path(backup_path) if backup_path else self.project_path / "backup_original"
        self.processed_files = 0
        self.instrumented_functions = 0
        self.errors = []
        
    def create_backup(self):
        """Cria backup completo do projeto antes da instrumentação"""
        if self.backup_path.exists():
            shutil.rmtree(self.backup_path)
            
        print(f"📦 Criando backup em: {self.backup_path}")
        shutil.copytree(self.project_path, self.backup_path, 
                       ignore=shutil.ignore_patterns('backup_*', '*.git*'))
        print("✅ Backup criado com sucesso!")
        
    def find_functions(self, content):
        """Encontra todas as User Functions e Static Functions no conteúdo"""
        functions = []
        
        # Regex para User Function
        user_pattern = r'^(\s*User\s+Function\s+)(\w+)(\s*\([^)]*\))'
        user_matches = re.finditer(user_pattern, content, re.MULTILINE | re.IGNORECASE)
        
        for match in user_matches:
            functions.append({
                'type': 'user_function',
                'name': match.group(2),
                'start': match.start(),
                'end': match.end(),
                'full_match': match.group(0),
                'line_start': content[:match.start()].count('\n') + 1
            })
        
        # Regex para Static Function
        static_pattern = r'^(\s*Static\s+Function\s+)(\w+)(\s*\([^)]*\))'
        static_matches = re.finditer(static_pattern, content, re.MULTILINE | re.IGNORECASE)
        
        for match in static_matches:
            functions.append({
                'type': 'static_function',
                'name': match.group(2),
                'start': match.start(),
                'end': match.end(),
                'full_match': match.group(0),
                'line_start': content[:match.start()].count('\n') + 1
            })
        
        # Ordena por posição no arquivo (do fim para o início para não afetar posições)
        functions.sort(key=lambda x: x['start'], reverse=True)
        
        return functions
    
    def is_already_instrumented(self, content, function_info):
        """Verifica se uma função já está instrumentada"""
        func_start = function_info['end']
        
        # Pega as próximas 5 linhas após a declaração da função
        lines_after = content[func_start:].split('\n')[:5]
        
        # Verifica se alguma linha contém U_TrackExecution
        for line in lines_after:
            if 'U_TrackExecution' in line:
                return True
        
        return False
    
    def get_function_indentation(self, content, function_info):
        """Detecta a indentação da função (método removido - usando padrão)"""
        return "    "  # 4 espaços padrão
    
    def instrument_function(self, content, function_info, file_name):
        """Instrumenta uma função específica"""
        
        # Verifica se já está instrumentada
        if self.is_already_instrumented(content, function_info):
            return content, False
        
        # Encontra o final da declaração da função (incluindo quebra de linha)
        func_end = function_info['end']
        
        # Encontra a próxima quebra de linha após a declaração
        next_newline = content.find('\n', func_end)
        if next_newline == -1:
            next_newline = len(content)
        
        # Posição onde vamos inserir (depois da quebra de linha)
        insert_position = next_newline + 1
        
        # Gera a linha de instrumentação com quebra de linha
        indent = "    "  # 4 espaços padrão
        
        if function_info['type'] == 'user_function':
            track_line = f"{indent}U_TrackExecution(\"{function_info['name'].upper()}\", \"{function_info['name'].upper()}\")\n"
        else:  # static_function
            file_base = Path(file_name).stem.upper()
            track_line = f"{indent}U_TrackExecution(\"{file_base}\", \"{function_info['name'].upper()}\")\n"
        
        # Insere a linha na posição correta
        new_content = content[:insert_position] + track_line + content[insert_position:]
        
        return new_content, True
    
    def process_file(self, file_path):
        """Processa um arquivo individual"""
        try:
            print(f"  🔍 Analisando: {file_path.name}")
            
            # Lê o arquivo
            with open(file_path, 'r', encoding='latin-1') as f:
                original_content = f.read()
            
            content = original_content
            
            # Encontra todas as funções
            functions = self.find_functions(content)
            
            if not functions:
                print(f"    ⏭️  Nenhuma User Function ou Static Function encontrada")
                return False
            
            print(f"    📋 Encontradas {len(functions)} funções:")
            
            instrumented_count = 0
            
            # Instrumenta cada função (do fim para o início)
            for func_info in functions:
                func_display = f"{func_info['type'].replace('_', ' ').title()}: {func_info['name']}"
                
                new_content, instrumented = self.instrument_function(content, func_info, file_path.name)
                
                if instrumented:
                    content = new_content
                    instrumented_count += 1
                    print(f"      ✅ {func_display} - Instrumentada")
                else:
                    print(f"      ⏭️  {func_display} - Já instrumentada")
            
            # Salva apenas se houve modificações
            if content != original_content:
                with open(file_path, 'w', encoding='latin-1') as f:
                    f.write(content)
                
                self.instrumented_functions += instrumented_count
                print(f"    💾 Arquivo salvo com {instrumented_count} instrumentações")
                return True
            else:
                print(f"    ⏭️  Nenhuma modificação necessária")
                return False
                
        except Exception as e:
            error_msg = f"Erro ao processar {file_path}: {str(e)}"
            self.errors.append(error_msg)
            print(f"    ❌ {error_msg}")
            return False
    
    def instrument_project(self):
        """Instrumenta todo o projeto"""
        print("🚀 Iniciando instrumentação automática do projeto...")
        print(f"📁 Pasta do projeto: {self.project_path}")
        
        # Cria backup
        self.create_backup()
        
        # Busca arquivos .prw e .tlpp (case-insensitive)
        code_files = []
        extensions = ['*.prw', '*.PRW', '*.tlpp', '*.TLPP']
        
        for ext in extensions:
            code_files.extend(list(self.project_path.rglob(ext)))
        
        # Remove duplicatas
        code_files = list(set(code_files))
        
        print(f"\n📋 Encontrados {len(code_files)} arquivos (.prw/.PRW e .tlpp/.TLPP)")
        
        # Processa cada arquivo
        print("\n🔧 Processando arquivos:")
        modified_files = 0
        
        for file_path in code_files:
            # Pula arquivos de backup
            if 'backup' in str(file_path).lower():
                continue
            
            if self.process_file(file_path):
                modified_files += 1
                self.processed_files += 1
        
        # Relatório final
        self.print_summary(modified_files)
    
    def print_summary(self, modified_files):
        """Imprime relatório final da instrumentação"""
        print(f"\n{'='*60}")
        print("📊 RELATÓRIO DE INSTRUMENTAÇÃO")
        print(f"{'='*60}")
        print(f"Arquivos processados: {self.processed_files}")
        print(f"Arquivos modificados: {modified_files}")
        print(f"Funções instrumentadas: {self.instrumented_functions}")
        
        if self.errors:
            print(f"\n⚠️  Erros encontrados ({len(self.errors)}):")
            for error in self.errors:
                print(f"  • {error}")
        
        print(f"\n💾 Backup disponível em: {self.backup_path}")
        print("\n✨ Instrumentação concluída!")
        print("\n📋 Próximos passos:")
        print("  1. Baixe o arquivo TRACKERCODE.PRW separadamente")
        print("  2. Compile o TRACKERCODE.PRW no Protheus")
        print("  3. Execute U_CreateTrackerTable() para criar a tabela")
        print("  4. Recompile os códigos instrumentados")
        print("  5. Aguarde alguns dias de uso para coletar dados")

def main():
    print("🎯 PROTHEUS CODE TRACKER - INSTRUMENTADOR AUTOMÁTICO")
    print("="*60)
    print("🔍 Busca apenas User Functions e Static Functions")
    print("⚠️  Functions padrão da Totvs serão ignoradas")
    print("📁 Suporta arquivos .PRW/.prw e .TLPP/.tlpp")
    print("="*60)
    
    # Solicita informações do usuário
    project_path = input("📁 Digite o caminho do projeto Protheus: ").strip()
    
    if not project_path:
        print("❌ Caminho não pode estar vazio!")
        return
    
    if not Path(project_path).exists():
        print("❌ Caminho não existe!")
        return
    
    # Confirma a instrumentação
    print(f"\n⚠️  ATENÇÃO: Este processo irá modificar TODOS os arquivos .prw/.PRW e .tlpp/.TLPP em:")
    print(f"   {project_path}")
    print(f"\n📋 Apenas User Functions e Static Functions serão instrumentadas")
    print(f"⛔ Functions padrão da Totvs serão ignoradas por segurança")
    print(f"\n📦 Um backup será criado automaticamente antes das modificações.")
    
    confirm = input("\n❓ Deseja continuar? (s/N): ").strip().lower()
    
    if confirm != 's':
        print("❌ Operação cancelada pelo usuário.")
        return
    
    # Executa instrumentação
    instrumenter = ProtheusInstrumenter(project_path)
    
    # Instrumenta o projeto
    instrumenter.instrument_project()

if __name__ == "__main__":
    main()
