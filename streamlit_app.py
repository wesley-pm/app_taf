import streamlit as st

from taf_core import resultado_taf

st.set_page_config(page_title="Calculadora TAF PMMS", layout="centered")

st.title("CALCULADORA TAF – PMMS")

st.markdown(
    "Simulador de nota conforme Portaria nº 042/PM-1/EMG/2018 "
    "(Protocolo Masculino e Feminino)."
)

sexo_label = st.radio("Gênero:", ["Masculino", "Feminino"])
sexo = "M" if sexo_label == "Masculino" else "F"

idade = st.number_input("Idade", min_value=18, max_value=70, value=30, step=1)

st.subheader("Informe seu desempenho nas provas")

# Corrida (sempre obrigatória)
corrida = st.number_input(
    "Corrida de 12 minutos (metros)",
    min_value=0,
    max_value=4000,
    step=10,
    value=2000,
)

col1, col2 = st.columns(2)

# --------------------------------------------------------------------
# Flexão de membros superiores
# --------------------------------------------------------------------
with col1:
    st.markdown("### Flexão de membros superiores")

    # Campos de repetição
    reps_barra = None
    reps_apoio = None

    # Masculino com menos de 36 anos -> obrigatoriamente barra
    if sexo == "M" and idade < 36:
        st.info("Para policiais masculinos com menos de 36 anos, "
                "a Portaria exige flexão na barra fixa.")
        tipo_flexao = "barra"
        reps_barra = st.number_input(
            "Número de repetições na barra",
            min_value=0,
            max_value=50,
            step=1,
            value=0,
        )

    # Feminino -> apenas apoio no solo
    elif sexo == "F":
        st.info("Para policiais femininas, o protocolo prevê apenas "
                "flexão de braço sobre o solo.")
        tipo_flexao = "apoio"
        reps_apoio = st.number_input(
            "Número de repetições de flexão no solo",
            min_value=0,
            max_value=200,
            step=1,
            value=0,
        )

    # Masculino com 36 anos ou mais -> pode escolher
    else:
        tipo_flexao_label = st.radio(
            "Escolha o exercício de flexão:",
            ["Flexão na barra", "Flexão no solo"],
            horizontal=True,
        )
        tipo_flexao = "barra" if "barra" in tipo_flexao_label else "apoio"

        reps_barra = st.number_input(
            "Número de repetições na barra",
            min_value=0,
            max_value=50,
            step=1,
            value=0,
        )
        reps_apoio = st.number_input(
            "Número de repetições de flexão no solo",
            min_value=0,
            max_value=200,
            step=1,
            value=0,
        )

# --------------------------------------------------------------------
# Abdominais
# --------------------------------------------------------------------
with col2:
    st.markdown("### Abdominais")

    tipo_abdominal_label = st.radio(
        "Escolha o tipo de abdominal:",
        ["Abdominal Carl-Up", "Abdominal Remador"],
        horizontal=True,
    )
    tipo_abdominal = "carlup" if "Carl-Up" in tipo_abdominal_label else "remador"

    reps_curlup = st.number_input(
        "Repetições de Abdominal Carl-Up",
        min_value=0,
        max_value=200,
        step=1,
        value=0,
    )
    reps_remador = st.number_input(
        "Repetições de Abdominal Remador",
        min_value=0,
        max_value=200,
        step=1,
        value=0,
    )

st.write("---")

# Nota mínima definida na Portaria (média 7,0)
NOTA_MINIMA = 7.0

colb1, colb2 = st.columns(2)
with colb1:
    calcular = st.button("Calcular nota")
with colb2:
    limpar = st.button("Limpar")

if limpar:
    st.rerun()

if calcular:
    media, notas, apto, zerou = resultado_taf(
        sexo=sexo,
        idade=idade,
        corrida_m=corrida,
        reps_apoio=reps_apoio,
        reps_barra=reps_barra,
        reps_curlup=reps_curlup,
        reps_remador=reps_remador,
        nota_minima=NOTA_MINIMA,
        tipo_flexao_escolhido=tipo_flexao,
        tipo_abdominal_escolhido=tipo_abdominal,
    )

    st.markdown("### Notas por prova")
    for prova, n in notas.items():
        st.write(f"{prova}: **{n:.1f}**")

    st.markdown(f"## Média final das provas: **{media:.1f}**")

    if zerou:
        st.warning("Observação: houve pelo menos uma prova com nota **0,0**.")

    if apto:
        st.success(
            "Situação: APROVADO no TAF "
            "(média ≥ 7,0 e nenhuma prova zerada)."
        )
    else:
        st.error(
            "Situação: INAPTO no TAF "
            "(média < 7,0 ou alguma prova com nota 0,0)."
        )
