"""
Sistema de Machine Learning para Análise de Produção Florestal
Floresta Cast LTDA

Este módulo pode ser:
1. Executado diretamente: python main.py
2. Importado por outros módulos (como dashboard.py)
"""

import os
from pathlib import Path
import pandas as pd
from datetime import datetime
import warnings

warnings.filterwarnings('ignore')


class ConfiguracaoCaminhos:
    """Configuração centralizada dos caminhos do sistema"""
    
    # Caminho do sistema principal
    SISTEMA = Path(r"D:\Meu Drive\Trabalho\Floresta_cast\ADM\P&D&I\Sistema")
    
    # Caminhos dos dados - Boletins (Consulta Completa)
    DADOS_CC = Path(r"D:\Meu Drive\Trabalho\Bracell\Relatorios\Boletins\CC")
    DADOS_CC_OS_ABERTA = DADOS_CC / "Atual" / "OS_aberta"
    DADOS_CC_OS_FECHADA = DADOS_CC / "Atual" / "OS_fechada"
    
    # Caminho dados recomendações
    DADOS_PD = Path(r"D:\Meu Drive\Trabalho\Bracell\Relatorios\P&D")
    
    # Caminho planejamento
    DADOS_PLANEJAMENTO = Path(r"D:\Meu Drive\Trabalho\Bracell\Relatorios\Planejamento")
    
    # Caminho de saída - Dashboard
    SAIDA_DASHBOARD = Path(r"D:\Meu Drive\Trabalho\Floresta_cast\ADM\P&D&I\Dashboard")


class CarregadorDados:
    """Classe responsável por carregar e validar dados dos arquivos Excel"""
    
    def __init__(self, config: ConfiguracaoCaminhos = None):
        self.config = config or ConfiguracaoCaminhos()
    
    def carregar_boletins_cc(self, verbose=True):
        """
        Carrega todos os arquivos CC*.xlsx dos diretórios de boletins
        Busca em:
        - Pasta principal CC
        - Subpasta OS_aberta
        - Subpasta OS_fechada
        
        Args:
            verbose (bool): Se True, exibe mensagens de progresso
            
        Returns:
            pd.DataFrame ou None: DataFrame com os dados carregados
        """
        # Definir diretórios para buscar
        diretorios = [
            self.config.DADOS_CC,
            self.config.DADOS_CC_OS_ABERTA,
            self.config.DADOS_CC_OS_FECHADA
        ]
        
        arquivos_cc = []
        for diretorio in diretorios:
            if diretorio.exists():
                arquivos_encontrados = list(diretorio.glob("CC*.xlsx"))
                arquivos_cc.extend(arquivos_encontrados)
                if verbose and len(arquivos_encontrados) > 0:
                    print(f"📁 {diretorio.name}: {len(arquivos_encontrados)} arquivo(s)")
        
        if not arquivos_cc:
            if verbose:
                print(f"⚠️ Nenhum arquivo CC*.xlsx encontrado nos diretórios:")
                for diretorio in diretorios:
                    print(f"   - {diretorio}")
            return None
        
        dataframes = []
        for arquivo in arquivos_cc:
            try:
                df = pd.read_excel(arquivo)
                df['arquivo_origem'] = arquivo.name
                df['pasta_origem'] = arquivo.parent.name  # Identificar origem (OS_aberta/OS_fechada)
                dataframes.append(df)
                if verbose:
                    print(f"✓ Carregado: {arquivo.parent.name}/{arquivo.name} ({len(df)} registros)")
            except Exception as e:
                if verbose:
                    print(f"✗ Erro ao carregar {arquivo.name}: {e}")
        
        if dataframes:
            df_completo = pd.concat(dataframes, ignore_index=True)
            if verbose:
                print(f"\n📊 Total de registros carregados: {len(df_completo):,}")
                print(f"📋 Total de arquivos: {len(arquivos_cc)}")
            return df_completo
        
        return None
    
    def carregar_plano_anual_silvicultura(self, verbose=True):
        """
        Carrega o arquivo PAS.xlsx (Plano Anual de Silvicultura)
        
        Args:
            verbose (bool): Se True, exibe mensagens de progresso
            
        Returns:
            pd.DataFrame ou None: DataFrame com os dados do PAS
        """
        arquivo_pas = self.config.DADOS_PLANEJAMENTO / "PAS.xlsx"
        
        if not arquivo_pas.exists():
            if verbose:
                print(f"⚠️ Arquivo PAS.xlsx não encontrado em {arquivo_pas}")
            return None
        
        try:
            df_pas = pd.read_excel(arquivo_pas)
            if verbose:
                print(f"✓ PAS.xlsx carregado: {len(df_pas)} registros")
                print(f"📋 Colunas disponíveis: {len(df_pas.columns)}")
            return df_pas
        except Exception as e:
            if verbose:
                print(f"✗ Erro ao carregar PAS.xlsx: {e}")
            return None
    
    def validar_estrutura_dados(self, df, colunas_esperadas):
        """Valida se o DataFrame possui as colunas esperadas"""
        colunas_faltantes = set(colunas_esperadas) - set(df.columns)
        
        if colunas_faltantes:
            print(f"⚠️ Colunas faltantes: {colunas_faltantes}")
            return False
        
        print("✓ Estrutura de dados validada")
        return True


class ProcessadorDados:
    """Classe para processamento e transformação de dados"""
    
    @staticmethod
    def limpar_dados(df):
        """Realiza limpeza básica dos dados"""
        # Remove duplicatas
        df = df.drop_duplicates()
        
        # Informações sobre valores ausentes
        valores_ausentes = df.isnull().sum()
        if valores_ausentes.sum() > 0:
            print(f"\n📉 Valores ausentes detectados:")
            print(valores_ausentes[valores_ausentes > 0])
        
        return df
    
    @staticmethod
    def preparar_para_ml(df):
        """Prepara dados para modelos de machine learning"""
        print("🔧 Preparando dados para ML...")
        # TODO: Implementar pré-processamento específico
        return df


class GeradorDashboard:
    """Classe para geração de visualizações e dashboard"""
    
    def __init__(self, config: ConfiguracaoCaminhos = None):
        self.config = config or ConfiguracaoCaminhos()
    
    def exportar_manual(self, df, nome_arquivo="manual.xlsx"):
        """Exporta dados processados para o dashboard"""
        caminho_saida = self.config.SAIDA_DASHBOARD / nome_arquivo
        
        try:
            # Criar diretório se não existir
            self.config.SAIDA_DASHBOARD.mkdir(parents=True, exist_ok=True)
            
            df.to_excel(caminho_saida, index=False)
            print(f"✓ Arquivo exportado: {caminho_saida}")
            return True
        except Exception as e:
            print(f"✗ Erro ao exportar: {e}")
            return False


def main():
    """Função principal - Execução em modo batch"""
    print("=" * 60)
    print("🌲 Sistema de Análise Florestal - Floresta Cast LTDA")
    print("=" * 60)
    print(f"📅 Execução: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    
    # Inicializar configuração
    config = ConfiguracaoCaminhos()
    
    # Inicializar componentes
    carregador = CarregadorDados(config)
    processador = ProcessadorDados()
    dashboard = GeradorDashboard(config)
    
    # 1. Carregar dados dos boletins
    print("\n📂 CARREGANDO DADOS DE BOLETINS (CC)...")
    print("-" * 60)
    df_boletins = carregador.carregar_boletins_cc()
    
    # 2. Carregar Plano Anual de Silvicultura
    print("\n📂 CARREGANDO PLANO ANUAL DE SILVICULTURA (PAS)...")
    print("-" * 60)
    df_pas = carregador.carregar_plano_anual_silvicultura()
    
    # 3. Processar dados
    if df_boletins is not None:
        print("\n🔄 PROCESSANDO DADOS...")
        print("-" * 60)
        df_boletins_limpo = processador.limpar_dados(df_boletins)
    
    # 4. Preparar para ML (a ser implementado)
    print("\n🤖 PREPARANDO MODELOS DE MACHINE LEARNING...")
    print("-" * 60)
    print("⏳ Em desenvolvimento...")
    
    # 5. Gerar visualizações e dashboard (a ser implementado)
    print("\n📊 GERANDO DASHBOARD...")
    print("-" * 60)
    print("⏳ Em desenvolvimento...")
    print("💡 Execute: streamlit run dashboard.py")
    
    print("\n" + "=" * 60)
    print("✅ Execução concluída!")
    print("=" * 60)


if __name__ == "__main__":
    # Este bloco só executa quando o arquivo é executado diretamente
    main()
else:
    # Quando importado, apenas exibe mensagem informativa
    print("📦 Módulo main.py importado com sucesso")