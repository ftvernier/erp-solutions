"""
Protheus Code Fixer - Release 2510
Ferramenta para identificar e sugerir correções em código ADVPL/TLPP
que usa atribuição direta a cEmpAnt e __cUserId
Autor: Fernando Vernier 
"""

import os
import re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Optional
import threading
from datetime import datetime


@dataclass
class CodeIssue:
    """Representa um problema encontrado no código"""
    file_path: str
    line_number: int
    line_content: str
    issue_type: str  # 'cEmpAnt' ou '__cUserId'
    suggestion: str
    function_name: Optional[str] = None
    assigned_value: Optional[str] = None


class ProtheusCodeAnalyzer:
    """Analisador de código Protheus"""
    
    def __init__(self):
        # Padrões para detectar atribuições diretas
        self.patterns = {
            'cEmpAnt': [
                re.compile(r'^\s*cEmpAnt\s*:=\s*(.+)', re.IGNORECASE),
                re.compile(r'^\s*cEmpAnt\s*=\s*(.+)', re.IGNORECASE),
            ],
            '__cUserId': [
                re.compile(r'^\s*__cUserId\s*:=\s*(.+)', re.IGNORECASE),
                re.compile(r'^\s*__cUserId\s*=\s*(.+)', re.IGNORECASE),
            ]
        }
        # Padrão para detectar declaração de função
        self.function_pattern = re.compile(
            r'^\s*(?:User\s+)?(?:Static\s+)?Function\s+(\w+)',
            re.IGNORECASE
        )
    
    def analyze_file(self, file_path: str) -> List[CodeIssue]:
        """Analisa um arquivo e retorna lista de problemas encontrados"""
        issues = []
        current_function = None
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line in enumerate(lines, start=1):
                # Detecta declaração de função
                func_match = self.function_pattern.match(line)
                if func_match:
                    current_function = func_match.group(1)
                
                # Ignora comentários
                if self._is_comment(line):
                    continue
                
                # Verifica cEmpAnt
                for pattern in self.patterns['cEmpAnt']:
                    match = pattern.search(line)
                    if match:
                        assigned_value = match.group(1).strip() if match.lastindex else None
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=line_num,
                            line_content=line.strip(),
                            issue_type='cEmpAnt',
                            suggestion=self._get_cempant_suggestion(),
                            function_name=current_function,
                            assigned_value=assigned_value
                        ))
                
                # Verifica __cUserId
                for pattern in self.patterns['__cUserId']:
                    match = pattern.search(line)
                    if match:
                        assigned_value = match.group(1).strip() if match.lastindex else None
                        issues.append(CodeIssue(
                            file_path=file_path,
                            line_number=line_num,
                            line_content=line.strip(),
                            issue_type='__cUserId',
                            suggestion=self._get_cuserid_suggestion(),
                            function_name=current_function,
                            assigned_value=assigned_value
                        ))
        
        except Exception as e:
            print(f"Erro ao analisar {file_path}: {str(e)}")
        
        return issues
    
    def _is_comment(self, line: str) -> bool:
        """Verifica se a linha é um comentário"""
        stripped = line.strip()
        return stripped.startswith('//') or stripped.startswith('*')
    
    def _get_cempant_suggestion(self) -> str:
        """Retorna sugestão de correção para cEmpAnt"""
        return """
SUGESTÃO DE CORREÇÃO:
Use RPCSetEnv() em uma nova thread:

StartJob("MinhaFuncao", GetEnvServer(), .F., "02", "01")

Static Function MinhaFuncao(cEmp, cFil)
    RPCSetEnv(cEmp, cFil)
    // Seu código aqui
    RPCClearEnv()
Return
"""
    
    def _get_cuserid_suggestion(self) -> str:
        """Retorna sugestão de correção para __cUserId"""
        return """
SUGESTÃO DE CORREÇÃO:
Use o sistema de tokens:

// Thread principal
Local cToken := totvs.framework.users.rpc.getAuthToken()
StartJob("ProcessaComToken", GetEnvServer(), .F., cToken)

// Nova thread
Static Function ProcessaComToken(cToken)
    totvs.framework.users.rpc.authByToken(cToken)
    // Seu código aqui
Return
"""
    
    def scan_directory(self, directory: str, extensions: List[str] = ['.prw', '.tlpp']) -> List[CodeIssue]:
        """Varre um diretório recursivamente procurando problemas"""
        all_issues = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if any(file.lower().endswith(ext) for ext in extensions):
                    file_path = os.path.join(root, file)
                    issues = self.analyze_file(file_path)
                    all_issues.extend(issues)
        
        return all_issues


class ProtheusCodeFixer:
    """Gera código corrigido seguindo padrão da documentação TOTVS"""
    
    def __init__(self):
        self.analyzer = ProtheusCodeAnalyzer()
    
    def fix_file(self, file_path: str, issues: List[CodeIssue]) -> str:
        """Gera arquivo corrigido com as alterações necessárias"""
        try:
            # Tenta diferentes encodings para ler o arquivo original
            content = None
            encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
            
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        content = f.read()
                        lines = content.splitlines(keepends=True)
                    break
                except UnicodeDecodeError:
                    continue
            
            if content is None:
                # Fallback: lê ignorando erros
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            
            # Agrupa issues por função
            issues_by_function = {}
            for issue in issues:
                func_name = issue.function_name or "UnknownFunction"
                if func_name not in issues_by_function:
                    issues_by_function[func_name] = []
                issues_by_function[func_name].append(issue)
            
            # Gera código corrigido
            fixed_content = self._generate_fixed_code(file_path, lines, issues_by_function)
            
            return fixed_content
        
        except Exception as e:
            return f"// ERRO ao gerar correção: {str(e)}\n"
    
    def _generate_fixed_code(self, file_path: str, lines: List[str], issues_by_function: dict) -> str:
        """Gera o código corrigido completo"""
        output = []
        
        # Header do arquivo corrigido
        output.append("/" + "=" * 79 + "\n")
        output.append(f"// ARQUIVO CORRIGIDO: {os.path.basename(file_path)}\n")
        output.append(f"// Gerado por: Protheus Code Fixer - Release 2510\n")
        output.append(f"// Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
        output.append(f"// Total de problemas corrigidos: {sum(len(issues) for issues in issues_by_function.values())}\n")
        output.append("/" + "=" * 79 + "\n\n")
        
        output.append("// ATENCAO: Este arquivo foi gerado automaticamente.\n")
        output.append("// REVISE o codigo antes de usar em producao!\n")
        output.append("// Correcoes baseadas na documentacao oficial TOTVS Release 2510\n\n")
        
        # Para cada função com problemas, gera a correção
        for func_name, func_issues in issues_by_function.items():
            output.append(self._generate_function_fix(func_name, func_issues, lines))
            output.append("\n")
        
        output.append("\n// FIM DO ARQUIVO CORRIGIDO\n")
        
        return "".join(output)
    
    def _generate_function_fix(self, func_name: str, issues: List[CodeIssue], lines: List[str]) -> str:
        """Gera correção para uma função específica"""
        output = []
        
        output.append("/" + "-" * 79 + "\n")
        output.append(f"// FUNCAO: {func_name}\n")
        output.append(f"// Problemas encontrados: {len(issues)}\n")
        
        for issue in issues:
            output.append(f"//   Linha {issue.line_number}: {issue.issue_type} := {issue.assigned_value}\n")
        
        output.append("/" + "-" * 79 + "\n\n")
        
        # Se for cEmpAnt, aplica correção com StartJob + RPCSetEnv
        if any(issue.issue_type == 'cEmpAnt' for issue in issues):
            output.append(self._generate_cempant_fix(func_name, issues, lines))
        
        # Se for __cUserId, aplica correção com tokens
        elif any(issue.issue_type == '__cUserId' for issue in issues):
            output.append(self._generate_cuserid_fix(func_name, issues, lines))
        
        return "".join(output)
    
    def _generate_cempant_fix(self, func_name: str, issues: List[CodeIssue], lines: List[str]) -> str:
        """Gera correção para cEmpAnt usando StartJob + RPCSetEnv"""
        output = []
        
        # Pega o valor sendo atribuído (primeiro issue como referência)
        first_issue = issues[0]
        empresa_var = first_issue.assigned_value or '"01"'
        
        # Limpa o valor (remove comentários inline, espaços extras)
        if '//' in empresa_var:
            empresa_var = empresa_var.split('//')[0].strip()
        
        # Função principal modificada (chama a Job)
        output.append(f"// CODIGO CORRIGIDO - Funcao Principal\n")
        output.append(f"User Function {func_name}()\n")
        output.append(f"    // Correcao aplicada conforme documentacao TOTVS Release 2510\n")
        output.append(f"    // Secao: 1. Rotinas ADVPL em Geral\n")
        output.append(f"    // Solucao: Uso de StartJob + RPCSetEnv em nova thread\n\n")
        output.append(f"    // Inicia processamento em nova thread\n")
        output.append(f"    StartJob(\"U_{func_name}Job\", GetEnvServer(), .F., {empresa_var}, cFilAnt)\n\n")
        output.append(f"    // Aguarda conclusao (se necessario)\n")
        output.append(f"    // TODO: Implementar controle de conclusao se necessario\n\n")
        output.append(f"Return .T.\n\n")
        
        # Função Job (onde o código original vai)
        output.append(f"// Nova funcao executada em thread separada\n")
        output.append(f"Static Function U_{func_name}Job(cEmp, cFil)\n")
        output.append(f"    // Prepara ambiente conforme empresa/filial recebida\n")
        output.append(f"    RPCSetEnv(cEmp, cFil)\n\n")
        output.append(f"    // TODO: Mover o codigo original da funcao {func_name} para aqui\n")
        output.append(f"    // O codigo que estava entre as linhas com problemas deve vir aqui\n\n")
        
        # Mostra as linhas problemáticas como referência
        output.append(f"    // CODIGO ORIGINAL (comentado para referencia):\n")
        for issue in issues:
            line_idx = issue.line_number - 1
            if 0 <= line_idx < len(lines):
                # Remove acentuação da linha original para evitar problemas
                original_line = lines[line_idx].strip()
                output.append(f"    // Linha {issue.line_number}: {original_line}\n")
        
        output.append(f"\n    // Limpa ambiente ao finalizar\n")
        output.append(f"    RPCClearEnv()\n\n")
        output.append(f"Return .T.\n")
        
        return "".join(output)
    
    def _generate_cuserid_fix(self, func_name: str, issues: List[CodeIssue], lines: List[str]) -> str:
        """Gera correção para __cUserId usando sistema de tokens"""
        output = []
        
        output.append(f"// CODIGO CORRIGIDO - Sistema de Tokens\n")
        output.append(f"User Function {func_name}()\n")
        output.append(f"    // Correcao aplicada conforme documentacao TOTVS Release 2510\n")
        output.append(f"    // Secao: 2. Transferencia de Credenciais de Usuario Entre Threads\n")
        output.append(f"    // Solucao: Uso de sistema de tokens\n\n")
        output.append(f"    Local cToken := totvs.framework.users.rpc.getAuthToken()\n\n")
        output.append(f"    // Inicia processamento em nova thread com token\n")
        output.append(f"    StartJob(\"U_{func_name}Job\", GetEnvServer(), .F., cToken)\n\n")
        output.append(f"Return .T.\n\n")
        
        output.append(f"// Nova funcao executada em thread separada\n")
        output.append(f"Static Function U_{func_name}Job(cToken)\n")
        output.append(f"    // Autentica usando o token recebido\n")
        output.append(f"    totvs.framework.users.rpc.authByToken(cToken)\n\n")
        output.append(f"    // TODO: Mover o codigo original da funcao {func_name} para aqui\n\n")
        
        # Mostra as linhas problemáticas como referência
        output.append(f"    // CODIGO ORIGINAL (comentado para referencia):\n")
        for issue in issues:
            line_idx = issue.line_number - 1
            if 0 <= line_idx < len(lines):
                original_line = lines[line_idx].strip()
                output.append(f"    // Linha {issue.line_number}: {original_line}\n")
        
        output.append(f"\nReturn .T.\n")
        
        return "".join(output)


class ProtheusCodeFixerGUI:
    """Interface gráfica da aplicação"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Protheus Code Fixer - Release 2510")
        self.root.geometry("1200x800")
        
        self.analyzer = ProtheusCodeAnalyzer()
        self.fixer = ProtheusCodeFixer()
        self.current_issues = []
        
        self._setup_ui()
        
    def _setup_ui(self):
        """Configura a interface do usuário"""
        
        # Frame superior - Seleção de diretório
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(fill=tk.X)
        
        ttk.Label(top_frame, text="Diretório dos fontes:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
        
        self.dir_entry = ttk.Entry(top_frame, width=60)
        self.dir_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        
        ttk.Button(top_frame, text="Procurar", command=self._browse_directory).pack(side=tk.LEFT, padx=5)
        ttk.Button(top_frame, text="Analisar", command=self._start_analysis, style='Accent.TButton').pack(side=tk.LEFT, padx=5)
        
        # Frame de opções
        options_frame = ttk.LabelFrame(self.root, text="Opções", padding="10")
        options_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.check_prw = tk.BooleanVar(value=True)
        self.check_tlpp = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(options_frame, text="Arquivos .PRW", variable=self.check_prw).pack(side=tk.LEFT, padx=10)
        ttk.Checkbutton(options_frame, text="Arquivos .TLPP", variable=self.check_tlpp).pack(side=tk.LEFT, padx=10)
        
        # Frame de progresso
        progress_frame = ttk.Frame(self.root, padding="10")
        progress_frame.pack(fill=tk.X)
        
        self.progress_label = ttk.Label(progress_frame, text="Pronto para análise")
        self.progress_label.pack(side=tk.LEFT, padx=5)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='indeterminate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Notebook com abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Aba 1: Resumo
        self._setup_summary_tab()
        
        # Aba 2: Detalhes
        self._setup_details_tab()
        
        # Aba 3: Relatório
        self._setup_report_tab()
        
        # Frame inferior - Estatísticas
        stats_frame = ttk.Frame(self.root, padding="10")
        stats_frame.pack(fill=tk.X)
        
        self.stats_label = ttk.Label(stats_frame, text="Nenhuma análise realizada", font=('Arial', 9))
        self.stats_label.pack(side=tk.LEFT)
        
        ttk.Button(stats_frame, text="Gerar Correções", command=self._generate_fixes, style='Accent.TButton').pack(side=tk.RIGHT, padx=5)
        ttk.Button(stats_frame, text="Exportar Relatório", command=self._export_report).pack(side=tk.RIGHT, padx=5)
        ttk.Button(stats_frame, text="Limpar", command=self._clear_results).pack(side=tk.RIGHT, padx=5)
    
    def _setup_summary_tab(self):
        """Configura aba de resumo"""
        summary_frame = ttk.Frame(self.notebook)
        self.notebook.add(summary_frame, text="📊 Resumo")
        
        # Treeview para resumo por arquivo
        columns = ('arquivo', 'problemas', 'cEmpAnt', '__cUserId')
        self.summary_tree = ttk.Treeview(summary_frame, columns=columns, show='tree headings')
        
        self.summary_tree.heading('arquivo', text='Arquivo')
        self.summary_tree.heading('problemas', text='Total Problemas')
        self.summary_tree.heading('cEmpAnt', text='cEmpAnt')
        self.summary_tree.heading('__cUserId', text='__cUserId')
        
        self.summary_tree.column('arquivo', width=400)
        self.summary_tree.column('problemas', width=120, anchor='center')
        self.summary_tree.column('cEmpAnt', width=100, anchor='center')
        self.summary_tree.column('__cUserId', width=100, anchor='center')
        
        scrollbar = ttk.Scrollbar(summary_frame, orient=tk.VERTICAL, command=self.summary_tree.yview)
        self.summary_tree.configure(yscrollcommand=scrollbar.set)
        
        self.summary_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _setup_details_tab(self):
        """Configura aba de detalhes"""
        details_frame = ttk.Frame(self.notebook)
        self.notebook.add(details_frame, text="🔍 Detalhes")
        
        # Treeview para detalhes
        columns = ('arquivo', 'linha', 'tipo', 'codigo')
        self.details_tree = ttk.Treeview(details_frame, columns=columns, show='tree headings')
        
        self.details_tree.heading('arquivo', text='Arquivo')
        self.details_tree.heading('linha', text='Linha')
        self.details_tree.heading('tipo', text='Tipo')
        self.details_tree.heading('codigo', text='Código')
        
        self.details_tree.column('arquivo', width=300)
        self.details_tree.column('linha', width=80, anchor='center')
        self.details_tree.column('tipo', width=100, anchor='center')
        self.details_tree.column('codigo', width=500)
        
        scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=self.details_tree.yview)
        self.details_tree.configure(yscrollcommand=scrollbar.set)
        
        self.details_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind para mostrar sugestão
        self.details_tree.bind('<Double-Button-1>', self._show_suggestion)
    
    def _setup_report_tab(self):
        """Configura aba de relatório"""
        report_frame = ttk.Frame(self.notebook)
        self.notebook.add(report_frame, text="📝 Relatório Completo")
        
        self.report_text = scrolledtext.ScrolledText(report_frame, wrap=tk.WORD, font=('Courier', 9))
        self.report_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def _browse_directory(self):
        """Abre diálogo para selecionar diretório"""
        directory = filedialog.askdirectory(title="Selecione o diretório dos fontes")
        if directory:
            self.dir_entry.delete(0, tk.END)
            self.dir_entry.insert(0, directory)
    
    def _start_analysis(self):
        """Inicia análise em thread separada"""
        directory = self.dir_entry.get()
        
        if not directory or not os.path.isdir(directory):
            messagebox.showerror("Erro", "Por favor, selecione um diretório válido!")
            return
        
        # Inicia análise em thread separada
        thread = threading.Thread(target=self._run_analysis, args=(directory,))
        thread.daemon = True
        thread.start()
    
    def _run_analysis(self, directory: str):
        """Executa análise do diretório"""
        self.progress_bar.start()
        self.progress_label.config(text="Analisando arquivos...")
        
        # Determina extensões a analisar
        extensions = []
        if self.check_prw.get():
            extensions.append('.prw')
        if self.check_tlpp.get():
            extensions.append('.tlpp')
        
        if not extensions:
            self.root.after(0, lambda: messagebox.showwarning("Aviso", "Selecione pelo menos um tipo de arquivo!"))
            self.progress_bar.stop()
            return
        
        # Analisa diretório
        self.current_issues = self.analyzer.scan_directory(directory, extensions)
        
        # Atualiza UI na thread principal
        self.root.after(0, self._update_results)
    
    def _update_results(self):
        """Atualiza interface com resultados"""
        self.progress_bar.stop()
        self.progress_label.config(text="Análise concluída!")
        
        # Limpa resultados anteriores
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        self.report_text.delete(1.0, tk.END)
        
        if not self.current_issues:
            messagebox.showinfo("Sucesso", "✅ Nenhum problema encontrado!\n\nSeu código está compatível com o Release 2510.")
            self.stats_label.config(text="✅ Nenhum problema encontrado")
            return
        
        # Agrupa por arquivo
        files_summary = {}
        for issue in self.current_issues:
            if issue.file_path not in files_summary:
                files_summary[issue.file_path] = {'cEmpAnt': 0, '__cUserId': 0}
            files_summary[issue.file_path][issue.issue_type] += 1
        
        # Preenche resumo
        for file_path, counts in files_summary.items():
            total = counts['cEmpAnt'] + counts['__cUserId']
            file_name = os.path.basename(file_path)
            self.summary_tree.insert('', tk.END, values=(file_name, total, counts['cEmpAnt'], counts['__cUserId']))
        
        # Preenche detalhes
        for issue in self.current_issues:
            file_name = os.path.basename(issue.file_path)
            self.details_tree.insert('', tk.END, values=(
                file_name,
                issue.line_number,
                issue.issue_type,
                issue.line_content
            ))
        
        # Gera relatório
        self._generate_report()
        
        # Atualiza estatísticas
        total_files = len(files_summary)
        total_issues = len(self.current_issues)
        cempant_count = sum(1 for i in self.current_issues if i.issue_type == 'cEmpAnt')
        cuserid_count = sum(1 for i in self.current_issues if i.issue_type == '__cUserId')
        
        self.stats_label.config(
            text=f"⚠️ {total_issues} problemas encontrados em {total_files} arquivo(s) | "
                 f"cEmpAnt: {cempant_count} | __cUserId: {cuserid_count}"
        )
        
        messagebox.showwarning(
            "Problemas Encontrados",
            f"⚠️ Foram encontrados {total_issues} problema(s) em {total_files} arquivo(s).\n\n"
            f"Verifique as abas para mais detalhes."
        )
    
    def _show_suggestion(self, event):
        """Mostra sugestão de correção ao dar duplo clique"""
        selection = self.details_tree.selection()
        if not selection:
            return
        
        item = self.details_tree.item(selection[0])
        values = item['values']
        
        # Encontra o issue correspondente
        file_name = values[0]
        line_number = values[1]
        
        for issue in self.current_issues:
            if os.path.basename(issue.file_path) == file_name and issue.line_number == line_number:
                # Mostra janela com sugestão
                self._show_suggestion_window(issue)
                break
    
    def _show_suggestion_window(self, issue: CodeIssue):
        """Exibe janela com sugestão de correção"""
        window = tk.Toplevel(self.root)
        window.title(f"Sugestão de Correção - Linha {issue.line_number}")
        window.geometry("700x500")
        
        # Informações do problema
        info_frame = ttk.LabelFrame(window, text="Problema Identificado", padding="10")
        info_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(info_frame, text=f"Arquivo: {os.path.basename(issue.file_path)}", font=('Arial', 9, 'bold')).pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Linha: {issue.line_number}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Tipo: {issue.issue_type}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Código: {issue.line_content}", foreground='red').pack(anchor=tk.W, pady=5)
        
        # Sugestão
        suggestion_frame = ttk.LabelFrame(window, text="Como Corrigir", padding="10")
        suggestion_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        suggestion_text = scrolledtext.ScrolledText(suggestion_frame, wrap=tk.WORD, font=('Courier', 9))
        suggestion_text.pack(fill=tk.BOTH, expand=True)
        suggestion_text.insert(1.0, issue.suggestion)
        suggestion_text.config(state=tk.DISABLED)
        
        ttk.Button(window, text="Fechar", command=window.destroy).pack(pady=10)
    
    def _generate_report(self):
        """Gera relatório textual completo"""
        report = "=" * 80 + "\n"
        report += "RELATÓRIO DE ANÁLISE - PROTHEUS CODE FIXER\n"
        report += "Release 2510 - Compatibilidade de Código\n"
        report += "=" * 80 + "\n\n"
        
        # Estatísticas
        total_files = len(set(issue.file_path for issue in self.current_issues))
        total_issues = len(self.current_issues)
        cempant_count = sum(1 for i in self.current_issues if i.issue_type == 'cEmpAnt')
        cuserid_count = sum(1 for i in self.current_issues if i.issue_type == '__cUserId')
        
        report += f"Total de arquivos analisados: {total_files}\n"
        report += f"Total de problemas encontrados: {total_issues}\n"
        report += f"  - Atribuições a cEmpAnt: {cempant_count}\n"
        report += f"  - Atribuições a __cUserId: {cuserid_count}\n\n"
        
        report += "=" * 80 + "\n"
        report += "DETALHAMENTO POR ARQUIVO\n"
        report += "=" * 80 + "\n\n"
        
        # Agrupa por arquivo
        files_issues = {}
        for issue in self.current_issues:
            if issue.file_path not in files_issues:
                files_issues[issue.file_path] = []
            files_issues[issue.file_path].append(issue)
        
        # Detalha cada arquivo
        for file_path, issues in sorted(files_issues.items()):
            report += f"\n📄 {file_path}\n"
            report += "-" * 80 + "\n"
            
            for issue in sorted(issues, key=lambda x: x.line_number):
                report += f"  Linha {issue.line_number:4d} | {issue.issue_type:12s} | {issue.line_content}\n"
            
            report += "\n"
        
        self.report_text.insert(1.0, report)
    
    def _export_report(self):
        """Exporta relatório para arquivo"""
        if not self.current_issues:
            messagebox.showwarning("Aviso", "Nenhum relatório para exportar!")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Salvar Relatório",
            defaultextension=".txt",
            filetypes=[("Arquivo de Texto", "*.txt"), ("Todos os arquivos", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(self.report_text.get(1.0, tk.END))
                messagebox.showinfo("Sucesso", f"Relatório exportado com sucesso!\n\n{file_path}")
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao exportar relatório:\n{str(e)}")
    
    def _clear_results(self):
        """Limpa resultados da análise"""
        for item in self.summary_tree.get_children():
            self.summary_tree.delete(item)
        for item in self.details_tree.get_children():
            self.details_tree.delete(item)
        self.report_text.delete(1.0, tk.END)
        self.current_issues = []
        self.stats_label.config(text="Nenhuma análise realizada")
        self.progress_label.config(text="Pronto para análise")
    
    def _generate_fixes(self):
        """Gera arquivos corrigidos para os problemas encontrados"""
        if not self.current_issues:
            messagebox.showwarning("Aviso", "Nenhum problema para corrigir!\n\nFaça uma análise primeiro.")
            return
        
        # Solicita diretório de saída
        output_dir = filedialog.askdirectory(title="Selecione o diretório para salvar os arquivos corrigidos")
        
        if not output_dir:
            return
        
        try:
            # Agrupa issues por arquivo
            issues_by_file = {}
            for issue in self.current_issues:
                if issue.file_path not in issues_by_file:
                    issues_by_file[issue.file_path] = []
                issues_by_file[issue.file_path].append(issue)
            
            # Gera arquivo corrigido para cada arquivo problemático
            fixed_files = []
            for file_path, issues in issues_by_file.items():
                # Gera código corrigido
                fixed_content = self.fixer.fix_file(file_path, issues)
                
                # Define nome do arquivo de saída
                original_name = os.path.basename(file_path)
                name_without_ext = os.path.splitext(original_name)[0]
                extension = os.path.splitext(original_name)[1]
                output_filename = f"{name_without_ext}_FIXED{extension}"
                output_path = os.path.join(output_dir, output_filename)
                
                # Salva arquivo corrigido com UTF-8 BOM para compatibilidade Windows
                with open(output_path, 'w', encoding='utf-8-sig') as f:
                    f.write(fixed_content)
                
                fixed_files.append(output_filename)
            
            # Mostra resultado
            files_list = "\n".join(f"  • {f}" for f in fixed_files)
            messagebox.showinfo(
                "Correções Geradas com Sucesso!",
                f"✅ {len(fixed_files)} arquivo(s) corrigido(s) gerado(s):\n\n"
                f"{files_list}\n\n"
                f"Local: {output_dir}\n\n"
                f"⚠️ IMPORTANTE: Revise o código antes de usar em produção!"
            )
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao gerar correções:\n{str(e)}")
    
    def run(self):
        """Inicia a aplicação"""
        self.root.mainloop()


if __name__ == "__main__":
    app = ProtheusCodeFixerGUI()
    app.run()
