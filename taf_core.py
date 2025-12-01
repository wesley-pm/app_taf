from pathlib import Path
from typing import Dict, Tuple

import pandas as pd

BASE_DIR = Path(__file__).parent

# Nomes das colunas exatamente como estão no CSV
COL_CORRIDA   = "Correr 12 min      Metros"
COL_APOIO     = "Exercícios \nde Apoio   Repetições"
COL_BARRA     = "Exercícios \nna Barra   Repetições"
COL_CURLUP    = "Abdominal \nCarl-Up      Repetições"
COL_REMADOR   = "Abdominal \nremador      Repetições"

# Colunas de nota por faixa etária
FAIXA_MAP = {
    "ate_25":   "Faixa etária Até 25",
    "26_30":    "Faixa etária 26 a 30",
    "31_35":    "Faixa etária   31 a 35",
    "36_40":    "Faixa etária    36 a 40",
    "41_45":    "Faixa etária    41 a 45",
    "46_50":    "Faixa etária     46 a 50",
    "acima_51": "Faixa etária    Acima de 51",
}


def faixa_key(idade: int) -> str:
    if idade <= 25:
        return "ate_25"
    elif idade <= 30:
        return "26_30"
    elif idade <= 35:
        return "31_35"
    elif idade <= 40:
        return "36_40"
    elif idade <= 45:
        return "41_45"
    elif idade <= 50:
        return "46_50"
    else:
        return "acima_51"


def _prepara_tabela_exercicio(
    df: pd.DataFrame,
    col_valor: str,
    convert=None,
) -> pd.DataFrame:
    """
    Monta uma tabela simplificada com:
    - 'valor' (metros ou repetições)
    - colunas de nota por faixa etária
    """
    cols = [col_valor] + list(FAIXA_MAP.values())
    tmp = df[cols].dropna(subset=[col_valor])

    # Converte para a unidade que vamos usar no app
    if convert is not None:
        tmp["valor"] = tmp[col_valor].apply(convert)
    else:
        tmp["valor"] = tmp[col_valor]

    # Remove duplicados e ordena
    tmp = (
        tmp
        .drop_duplicates(subset=["valor"])
        .sort_values("valor")
        .reset_index(drop=True)
    )
    return tmp


# --- Carrega as duas tabelas originais da Portaria ---
df_m = pd.read_csv(BASE_DIR / "tabela_masculina.csv", sep=";")
df_f = pd.read_csv(BASE_DIR / "tabela_feminina.csv", sep=";")

# Corrida masculina está em km (1.00, 1.10, ...). Converto para metros.
TAB_M = {
    "corrida": _prepara_tabela_exercicio(
        df_m, COL_CORRIDA, convert=lambda x: int(round(x * 1000))
    ),
    "apoio":   _prepara_tabela_exercicio(df_m, COL_APOIO,   convert=int),
    "barra":   _prepara_tabela_exercicio(df_m, COL_BARRA,   convert=int),
    "curlup":  _prepara_tabela_exercicio(df_m, COL_CURLUP,  convert=int),
    "remador": _prepara_tabela_exercicio(df_m, COL_REMADOR, convert=int),
}

# Corrida feminina já está em metros (700, 750, ...).
TAB_F = {
    "corrida": _prepara_tabela_exercicio(df_f, COL_CORRIDA, convert=int),
    "apoio":   _prepara_tabela_exercicio(df_f, COL_APOIO,   convert=int),
    "barra":   _prepara_tabela_exercicio(df_f, COL_BARRA,   convert=int),
    "curlup":  _prepara_tabela_exercicio(df_f, COL_CURLUP,  convert=int),
    "remador": _prepara_tabela_exercicio(df_f, COL_REMADOR, convert=int),
}

TABELAS = {
    "M": TAB_M,
    "F": TAB_F,
}


def nota_prova(sexo: str, prova: str, desempenho: int | float, idade: int) -> float:
    """
    sexo: 'M' ou 'F'
    prova: 'corrida', 'apoio', 'barra', 'curlup', 'remador'
    desempenho:
        - corrida -> metros
        - demais -> número de repetições
    """
    tab = TABELAS[sexo][prova]
    faixa = faixa_key(idade)
    col_nota = FAIXA_MAP[faixa]

    elegiveis = tab[tab["valor"] <= desempenho]

    if elegiveis.empty:
        return 0.0

    # pega a linha com maior 'valor' ainda <= desempenho
    linha = elegiveis.iloc[-1]
    return float(linha[col_nota])


def resultado_taf(
    sexo: str,
    idade: int,
    corrida_m: int | float,
    reps_apoio: int | float | None,
    reps_barra: int | float | None,
    reps_curlup: int | float | None,
    reps_remador: int | float | None,
    nota_minima: float,
    tipo_flexao_escolhido: str,
    tipo_abdominal_escolhido: str,
) -> Tuple[float, Dict[str, float], bool, bool]:
    """
    Calcula o resultado do TAF conforme a Portaria:

    - 3 provas: corrida + 1 flexão + 1 abdominal
    - média aritmética das notas
    - se alguma prova for 0, INAPTO

    tipo_flexao_escolhido: 'barra' ou 'apoio'
    tipo_abdominal_escolhido: 'carlup' ou 'remador'

    Retorna:
        media, notas_por_prova, apto (True/False), zerou_alguma (True/False)
    """

    notas: Dict[str, float] = {}

    # Corrida (sempre obrigatória)
    nota_corrida = nota_prova(sexo, "corrida", corrida_m or 0, idade)
    notas["Corrida 12 min"] = nota_corrida

    # --- Flexão de membros superiores ---
    # Regra:
    # - Masculino < 36 anos: obrigatoriamente barra
    # - Feminino: apenas apoio no solo
    # - Masculino >= 36 anos: pode escolher (barra ou apoio)
    if sexo == "M" and idade < 36:
        tipo_flexao_efetivo = "barra"
    elif sexo == "F":
        tipo_flexao_efetivo = "apoio"
    else:
        tipo_flexao_efetivo = tipo_flexao_escolhido  # escolha do usuário

    if tipo_flexao_efetivo == "barra":
        valor = reps_barra or 0
        nota_flexao = nota_prova(sexo, "barra", valor, idade)
        notas["Flexão na barra"] = nota_flexao
    else:
        valor = reps_apoio or 0
        nota_flexao = nota_prova(sexo, "apoio", valor, idade)
        notas["Flexão de braço no solo"] = nota_flexao

    # --- Abdominais ---
    # Pode escolher Carl-up ou Remador (qualquer idade/sexo)
    if tipo_abdominal_escolhido == "remador":
        valor = reps_remador or 0
        nota_abd = nota_prova(sexo, "remador", valor, idade)
        notas["Abdominal remador"] = nota_abd
    else:
        valor = reps_curlup or 0
        nota_abd = nota_prova(sexo, "curlup", valor, idade)
        notas["Abdominal Carl-Up"] = nota_abd

    # --- Cálculo da média e regras finais ---
    lista_notas = list(notas.values())
    media = sum(lista_notas) / len(lista_notas) if lista_notas else 0.0

    zerou_alguma = any(n == 0 for n in lista_notas)
    apto = (media >= nota_minima) and not zerou_alguma

    return media, notas, apto, zerou_alguma

def desempenho_para_nota_minima(sexo: str, idade: int, nota_min: float = 7.0) -> Dict[str, int | None]:
    faixa = faixa_key(idade)
    col_nota = FAIXA_MAP[faixa]
    tab = TABELAS[sexo]

    resultados = {}
    for nome_exercicio, df in tab.items():
        filtro = df[df[col_nota] >= nota_min]
        if not filtro.empty:
            resultados[nome_exercicio] = int(filtro["valor"].min())
        else:
            resultados[nome_exercicio] = None
    return resultados


