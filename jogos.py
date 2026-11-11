"""
🎮 Fliperama Streamlit — vários jogos em um único arquivo.
Rodar localmente:  streamlit run jogos.py
"""
import json
import math
import random
import unicodedata

import chess
import requests
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Fliperama Streamlit", page_icon="🎮", layout="centered")
S = st.session_state


def css_botoes(altura_px: int, fonte_rem: float):
    """Deixa os botões do jogo atual largos e no tamanho certo."""
    st.markdown(
        f"""<style>
        div.stButton > button {{
            width: 100%; min-height: {altura_px}px; font-size: {fonte_rem}rem;
        }}
        </style>""",
        unsafe_allow_html=True,
    )


# =====================================================================
# 1) ADIVINHE O NÚMERO
# =====================================================================
NIVEIS_ADV = {"Fácil (1–50)": 50, "Médio (1–100)": 100, "Difícil (1–500)": 500}


def adv_novo(limite):
    S.adv_limite = limite
    S.adv_alvo = random.randint(1, limite)
    S.adv_tentativas = []
    S.adv_fim = False


def jogo_adivinha():
    nivel = st.radio("Dificuldade", list(NIVEIS_ADV), horizontal=True, key="adv_nivel")
    limite = NIVEIS_ADV[nivel]
    if S.get("adv_limite") != limite:
        adv_novo(limite)

    st.write(f"Pensei em um número entre **1 e {limite}**. Consegue descobrir?")

    if not S.adv_fim:
        with st.form("adv_form", clear_on_submit=True):
            palpite = st.number_input("Seu palpite", 1, limite, step=1)
            if st.form_submit_button("Chutar 🎯"):
                palpite = int(palpite)
                S.adv_tentativas.append(palpite)
                if palpite == S.adv_alvo:
                    S.adv_fim = True

    if S.adv_tentativas:
        ultimo = S.adv_tentativas[-1]
        if S.adv_fim:
            st.success(f"🎉 Acertou! Era **{S.adv_alvo}** — em {len(S.adv_tentativas)} tentativa(s).")
            st.balloons()
        elif ultimo < S.adv_alvo:
            st.info(f"⬆️ {ultimo} é **baixo**. Tente um número maior.")
        else:
            st.info(f"⬇️ {ultimo} é **alto**. Tente um número menor.")
        st.caption("Palpites: " + ", ".join(map(str, S.adv_tentativas)))

    if st.button("🔄 Novo jogo", key="adv_reset"):
        adv_novo(limite)
        st.rerun()


# =====================================================================
# 2) JOGO DA VELHA (contra o computador)
# =====================================================================
LINHAS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
          (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def velha_vencedor(b):
    for a, m, c in LINHAS:
        if b[a] and b[a] == b[m] == b[c]:
            return b[a]
    return "Empate" if all(b) else None


def minimax(b, jogador):
    v = velha_vencedor(b)
    if v == "O":
        return 1, None
    if v == "X":
        return -1, None
    if v == "Empate":
        return 0, None
    melhor = (-2, None) if jogador == "O" else (2, None)
    for i in range(9):
        if not b[i]:
            b[i] = jogador
            nota, _ = minimax(b, "X" if jogador == "O" else "O")
            b[i] = ""
            if (jogador == "O" and nota > melhor[0]) or (jogador == "X" and nota < melhor[0]):
                melhor = (nota, i)
    return melhor


def velha_jogada_pc(b, nivel):
    livres = [i for i in range(9) if not b[i]]
    chance_esperta = {"Fácil": 0.0, "Médio": 0.6, "Impossível": 1.0}[nivel]
    if random.random() < chance_esperta:
        return minimax(b, "O")[1]
    return random.choice(livres)


def velha_novo():
    S.velha_tab = [""] * 9
    S.velha_fim = None


def velha_click(i):
    b = S.velha_tab
    if b[i] or S.velha_fim:
        return
    b[i] = "X"
    S.velha_fim = velha_vencedor(b)
    if not S.velha_fim:
        b[velha_jogada_pc(b, S.velha_nivel)] = "O"
        S.velha_fim = velha_vencedor(b)
    if S.velha_fim:
        chave = {"X": "voce", "O": "pc", "Empate": "empate"}[S.velha_fim]
        S.velha_placar[chave] += 1


def jogo_velha():
    if "velha_tab" not in S:
        velha_novo()
        S.velha_placar = {"voce": 0, "pc": 0, "empate": 0}
    st.radio("Nível do computador", ["Fácil", "Médio", "Impossível"],
             index=1, horizontal=True, key="velha_nivel")

    p = S.velha_placar
    c1, c2, c3 = st.columns(3)
    c1.metric("Você (❌)", p["voce"])
    c2.metric("Empates", p["empate"])
    c3.metric("Computador (⭕)", p["pc"])

    css_botoes(90, 2.2)
    simbolo = {"X": "❌", "O": "⭕", "": "·"}
    for r in range(3):
        cols = st.columns(3)
        for c in range(3):
            i = r * 3 + c
            cols[c].button(simbolo[S.velha_tab[i]], key=f"velha_{i}",
                           on_click=velha_click, args=(i,),
                           disabled=bool(S.velha_tab[i] or S.velha_fim))

    fim = S.velha_fim
    if fim == "X":
        st.success("🎉 Você venceu!")
    elif fim == "O":
        st.error("🤖 O computador venceu!")
    elif fim == "Empate":
        st.warning("🤝 Deu velha!")

    if st.button("🔄 Nova partida", key="velha_reset"):
        velha_novo()
        st.rerun()


# =====================================================================
# 3) FORCA
# =====================================================================
PALAVRAS = {
    "Animais": ["ELEFANTE", "GIRAFA", "TUCANO", "CAPIVARA", "JACARE", "ONCA", "TAMANDUA", "PINGUIM"],
    "Frutas": ["ABACAXI", "JABUTICABA", "MANGA", "GOIABA", "MARACUJA", "ACEROLA", "PITANGA"],
    "Países": ["BRASIL", "ARGENTINA", "PORTUGAL", "JAPAO", "CANADA", "MEXICO", "AUSTRALIA"],
    "Tecnologia": ["PYTHON", "STREAMLIT", "GITHUB", "TECLADO", "INTERNET", "ALGORITMO"],
}
DESENHOS = [
    "  +---+\n      |\n      |\n      |\n     ===",
    "  +---+\n  O   |\n      |\n      |\n     ===",
    "  +---+\n  O   |\n  |   |\n      |\n     ===",
    "  +---+\n  O   |\n /|   |\n      |\n     ===",
    "  +---+\n  O   |\n /|\\  |\n      |\n     ===",
    "  +---+\n  O   |\n /|\\  |\n /    |\n     ===",
    "  +---+\n  O   |\n /|\\  |\n / \\  |\n     ===",
]
MAX_ERROS = len(DESENHOS) - 1


def forca_novo():
    S.forca_cat = random.choice(list(PALAVRAS))
    S.forca_palavra = random.choice(PALAVRAS[S.forca_cat])
    S.forca_letras = set()
    S.forca_erros = 0


def forca_chute(letra):
    if letra in S.forca_letras:
        return
    S.forca_letras.add(letra)
    if letra not in S.forca_palavra:
        S.forca_erros += 1


def jogo_forca():
    if "forca_palavra" not in S:
        forca_novo()

    palavra = S.forca_palavra
    venceu = all(l in S.forca_letras for l in palavra)
    perdeu = S.forca_erros >= MAX_ERROS

    col_desenho, col_info = st.columns([1, 2])
    col_desenho.code(DESENHOS[S.forca_erros], language=None)
    with col_info:
        st.write(f"**Dica:** {S.forca_cat}")
        mostra = " ".join(l if (l in S.forca_letras or perdeu) else "_" for l in palavra)
        st.markdown(f"### `{mostra}`")
        st.write(f"Erros: **{S.forca_erros}/{MAX_ERROS}**")

    if venceu:
        st.success("🎉 Você salvou o boneco!")
    elif perdeu:
        st.error(f"💀 Enforcado! A palavra era **{palavra}**.")
    else:
        css_botoes(42, 1.0)
        alfabeto = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        por_linha = 9
        for inicio in range(0, len(alfabeto), por_linha):
            cols = st.columns(por_linha)
            for j, letra in enumerate(alfabeto[inicio:inicio + por_linha]):
                cols[j].button(letra, key=f"forca_{letra}", on_click=forca_chute,
                               args=(letra,), disabled=letra in S.forca_letras)

    if st.button("🔄 Nova palavra", key="forca_reset"):
        forca_novo()
        st.rerun()


# =====================================================================
# 4) PEDRA, PAPEL E TESOURA
# =====================================================================
OPCOES = {"Pedra": "🪨", "Papel": "📄", "Tesoura": "✂️"}
GANHA_DE = {"Pedra": "Tesoura", "Papel": "Pedra", "Tesoura": "Papel"}


def ppt_jogar(escolha):
    pc = random.choice(list(OPCOES))
    if escolha == pc:
        res = "empate"
    elif GANHA_DE[escolha] == pc:
        res = "voce"
    else:
        res = "pc"
    S.ppt_placar[res] += 1
    S.ppt_ultimo = (escolha, pc, res)


def jogo_ppt():
    if "ppt_placar" not in S:
        S.ppt_placar = {"voce": 0, "pc": 0, "empate": 0}
        S.ppt_ultimo = None

    p = S.ppt_placar
    c1, c2, c3 = st.columns(3)
    c1.metric("Você", p["voce"])
    c2.metric("Empates", p["empate"])
    c3.metric("Computador", p["pc"])

    css_botoes(80, 1.4)
    cols = st.columns(3)
    for col, (nome, emoji) in zip(cols, OPCOES.items()):
        col.button(f"{emoji} {nome}", key=f"ppt_{nome}", on_click=ppt_jogar, args=(nome,))

    if S.ppt_ultimo:
        voce, pc, res = S.ppt_ultimo
        st.markdown(f"## {OPCOES[voce]} &nbsp; vs &nbsp; {OPCOES[pc]}")
        msg = {"voce": st.success, "pc": st.error, "empate": st.warning}[res]
        texto = {"voce": f"Você venceu! {voce} ganha de {pc}.",
                 "pc": f"Você perdeu! {pc} ganha de {voce}.",
                 "empate": "Empate!"}[res]
        msg(texto)

    if st.button("🔄 Zerar placar", key="ppt_reset"):
        del S["ppt_placar"]
        st.rerun()


# =====================================================================
# 5) JOGO DA MEMÓRIA
# =====================================================================
EMOJIS = ["🐶", "🐱", "🦊", "🐸", "🐵", "🦁", "🐼", "🐙"]


def mem_novo():
    cartas = EMOJIS * 2
    random.shuffle(cartas)
    S.mem_cartas = cartas
    S.mem_achados = set()
    S.mem_virados = []
    S.mem_jogadas = 0


def mem_click(i):
    if i in S.mem_achados or i in S.mem_virados:
        return
    if len(S.mem_virados) == 2:  # par errado ainda à mostra: esconde e segue
        S.mem_virados = []
    S.mem_virados.append(i)
    if len(S.mem_virados) == 2:
        S.mem_jogadas += 1
        a, b = S.mem_virados
        if S.mem_cartas[a] == S.mem_cartas[b]:
            S.mem_achados.update((a, b))
            S.mem_virados = []


def jogo_memoria():
    if "mem_cartas" not in S:
        mem_novo()

    st.write(f"Jogadas: **{S.mem_jogadas}** · Pares: **{len(S.mem_achados) // 2}/{len(EMOJIS)}**")
    css_botoes(75, 2.0)
    for r in range(4):
        cols = st.columns(4)
        for c in range(4):
            i = r * 4 + c
            visivel = i in S.mem_achados or i in S.mem_virados
            cols[c].button(S.mem_cartas[i] if visivel else "❓", key=f"mem_{i}",
                           on_click=mem_click, args=(i,), disabled=i in S.mem_achados)

    if len(S.mem_achados) == len(S.mem_cartas):
        st.success(f"🎉 Parabéns! Você terminou em {S.mem_jogadas} jogadas.")
        st.balloons()

    if st.button("🔄 Embaralhar de novo", key="mem_reset"):
        mem_novo()
        st.rerun()


# =====================================================================
# 6) XADREZ (contra o computador)
# =====================================================================
SIMBOLO_XQ = {chess.KING: "♚", chess.QUEEN: "♛", chess.ROOK: "♜",
              chess.BISHOP: "♝", chess.KNIGHT: "♞", chess.PAWN: "♟︎"}
VALOR = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
         chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
# Tabelas de posição (visão das brancas, linha 8 no topo)
PST = {
    chess.PAWN: [0, 0, 0, 0, 0, 0, 0, 0,
                 50, 50, 50, 50, 50, 50, 50, 50,
                 10, 10, 20, 30, 30, 20, 10, 10,
                 5, 5, 10, 25, 25, 10, 5, 5,
                 0, 0, 0, 20, 20, 0, 0, 0,
                 5, -5, -10, 0, 0, -10, -5, 5,
                 5, 10, 10, -20, -20, 10, 10, 5,
                 0, 0, 0, 0, 0, 0, 0, 0],
    chess.KNIGHT: [-50, -40, -30, -30, -30, -30, -40, -50,
                   -40, -20, 0, 0, 0, 0, -20, -40,
                   -30, 0, 10, 15, 15, 10, 0, -30,
                   -30, 5, 15, 20, 20, 15, 5, -30,
                   -30, 0, 15, 20, 20, 15, 0, -30,
                   -30, 5, 10, 15, 15, 10, 5, -30,
                   -40, -20, 0, 5, 5, 0, -20, -40,
                   -50, -40, -30, -30, -30, -30, -40, -50],
    chess.BISHOP: [-20, -10, -10, -10, -10, -10, -10, -20,
                   -10, 0, 0, 0, 0, 0, 0, -10,
                   -10, 0, 5, 10, 10, 5, 0, -10,
                   -10, 5, 5, 10, 10, 5, 5, -10,
                   -10, 0, 10, 10, 10, 10, 0, -10,
                   -10, 10, 10, 10, 10, 10, 10, -10,
                   -10, 5, 0, 0, 0, 0, 5, -10,
                   -20, -10, -10, -10, -10, -10, -10, -20],
    chess.ROOK: [0, 0, 0, 0, 0, 0, 0, 0,
                 5, 10, 10, 10, 10, 10, 10, 5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5,
                 0, 0, 0, 5, 5, 0, 0, 0],
    chess.QUEEN: [-20, -10, -10, -5, -5, -10, -10, -20,
                  -10, 0, 0, 0, 0, 0, 0, -10,
                  -10, 0, 5, 5, 5, 5, 0, -10,
                  -5, 0, 5, 5, 5, 5, 0, -5,
                  0, 0, 5, 5, 5, 5, 0, -5,
                  -10, 5, 5, 5, 5, 5, 0, -10,
                  -10, 0, 5, 0, 0, 0, 0, -10,
                  -20, -10, -10, -5, -5, -10, -10, -20],
    chess.KING: [-30, -40, -40, -50, -50, -40, -40, -30,
                 -30, -40, -40, -50, -50, -40, -40, -30,
                 -30, -40, -40, -50, -50, -40, -40, -30,
                 -30, -40, -40, -50, -50, -40, -40, -30,
                 -20, -30, -30, -40, -40, -30, -30, -20,
                 -10, -20, -20, -20, -20, -20, -20, -10,
                 20, 20, 0, 0, 0, 0, 20, 20,
                 20, 30, 10, 0, 0, 10, 30, 20],
}
MATE = 100_000
NIVEIS_XQ = {"Fácil": 1, "Médio": 2, "Difícil": 3}
PROMOCAO = {"Dama": chess.QUEEN, "Torre": chess.ROOK, "Bispo": chess.BISHOP, "Cavalo": chess.KNIGHT}
FIM_PT = {
    chess.Termination.CHECKMATE: "xeque-mate",
    chess.Termination.STALEMATE: "afogamento (empate)",
    chess.Termination.INSUFFICIENT_MATERIAL: "material insuficiente (empate)",
    chess.Termination.SEVENTYFIVE_MOVES: "regra dos 75 lances (empate)",
    chess.Termination.FIVEFOLD_REPETITION: "repetição (empate)",
    chess.Termination.FIFTY_MOVES: "regra dos 50 lances (empate)",
    chess.Termination.THREEFOLD_REPETITION: "tripla repetição (empate)",
}


def xq_avaliar(b):
    """Material + posição, do ponto de vista de quem joga."""
    s = 0
    for sq, p in b.piece_map().items():
        v = VALOR[p.piece_type] + PST[p.piece_type][sq ^ 56 if p.color else sq]
        s += v if p.color == chess.WHITE else -v
    return s if b.turn == chess.WHITE else -s


def xq_ordenar(b, lances):
    def nota(m):
        n = 0
        if b.is_capture(m):
            vitima = b.piece_at(m.to_square)
            n = 10 * (VALOR[vitima.piece_type] if vitima else 100) - VALOR[b.piece_at(m.from_square).piece_type]
        if m.promotion:
            n += 8000
        return -n
    return sorted(lances, key=nota)


def xq_quiescencia(b, alfa, beta, prof):
    parado = xq_avaliar(b)
    if parado >= beta:
        return beta
    alfa = max(alfa, parado)
    if prof == 0:
        return alfa
    for m in xq_ordenar(b, [m for m in b.legal_moves if b.is_capture(m)]):
        b.push(m)
        s = -xq_quiescencia(b, -beta, -alfa, prof - 1)
        b.pop()
        if s >= beta:
            return beta
        alfa = max(alfa, s)
    return alfa


def xq_negamax(b, prof, alfa, beta, ply):
    lances = list(b.legal_moves)
    if not lances:
        return -MATE + ply if b.is_check() else 0
    if b.is_insufficient_material() or b.halfmove_clock >= 100:
        return 0
    if prof == 0:
        return xq_quiescencia(b, alfa, beta, 4)
    melhor = -MATE * 2
    for m in xq_ordenar(b, lances):
        b.push(m)
        s = -xq_negamax(b, prof - 1, -beta, -alfa, ply + 1)
        b.pop()
        melhor = max(melhor, s)
        alfa = max(alfa, s)
        if alfa >= beta:
            break
    return melhor


def xq_melhor_lance(b, nivel):
    prof = NIVEIS_XQ[nivel]
    ruido = {"Fácil": 120, "Médio": 25, "Difícil": 0}[nivel]
    lances = list(b.legal_moves)
    random.shuffle(lances)
    melhor, melhor_nota = lances[0], -MATE * 3
    alfa = -MATE * 2
    for m in xq_ordenar(b, lances):
        b.push(m)
        s = -xq_negamax(b, prof - 1, -MATE * 2, -alfa + ruido, 1) + random.randint(-ruido, ruido)
        b.pop()
        if s > melhor_nota:
            melhor, melhor_nota = m, s
        if ruido == 0:
            alfa = max(alfa, s)
    return melhor


def xq_novo():
    S.xq_board = chess.Board()
    S.xq_sel = None
    S.xq_cor = chess.WHITE if S.get("xq_lado", "Brancas") == "Brancas" else chess.BLACK


def xq_click(sq):
    b = S.xq_board
    if b.outcome(claim_draw=True) or b.turn != S.xq_cor:
        return
    p = b.piece_at(sq)
    if p and p.color == S.xq_cor:
        S.xq_sel = None if S.xq_sel == sq else sq
        return
    if S.xq_sel is None:
        return
    m = chess.Move(S.xq_sel, sq)
    if b.piece_at(S.xq_sel).piece_type == chess.PAWN and chess.square_rank(sq) in (0, 7):
        m.promotion = PROMOCAO[S.xq_promo]
    if m in b.legal_moves:
        b.push(m)
    S.xq_sel = None


def xq_desfazer():
    b = S.xq_board
    if b.move_stack:
        b.pop()
    while b.move_stack and b.turn != S.xq_cor:
        b.pop()
    S.xq_sel = None


def xq_css(b):
    claro, escuro = "#f0d9b5", "#b58863"
    ultimo = b.move_stack[-1] if b.move_stack else None
    alvos = {m.to_square for m in b.legal_moves if m.from_square == S.xq_sel}
    rei_xeque = b.king(b.turn) if b.is_check() else None
    regras = ["""
    .st-key-xq_tab { max-width: 560px; margin: 0 auto; border: 6px solid #5c3d22; border-radius: 4px; }
    .st-key-xq_tab [data-testid="stVerticalBlock"] { gap: 0 !important; }
    .st-key-xq_tab [data-testid="stHorizontalBlock"] { flex-wrap: nowrap !important; gap: 0 !important; }
    .st-key-xq_tab [data-testid="stColumn"], .st-key-xq_tab [data-testid="column"] {
        min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }
    .st-key-xq_tab .stButton, .st-key-xq_tab .stButton > button { width: 100% !important; }
    .st-key-xq_tab button {
        aspect-ratio: 1 / 1; min-height: 0 !important; padding: 0 !important;
        border: none !important; border-radius: 0 !important; line-height: 1 !important;
        font-size: clamp(1.4rem, 6vw, 2.7rem) !important; font-variant-emoji: text; }
    .st-key-xq_tab button p { font-size: inherit !important; line-height: 1 !important; }
    .st-key-xq_tab button:focus { box-shadow: none !important; }
    """]
    for sq in chess.SQUARES:
        e_claro = (chess.square_file(sq) + chess.square_rank(sq)) % 2 == 1
        cor = claro if e_claro else escuro
        if ultimo and sq in (ultimo.from_square, ultimo.to_square):
            cor = "#cdd26a" if e_claro else "#aaa23a"
        if sq == S.xq_sel:
            cor = "#f6f669" if e_claro else "#dac34b"
        fundo = cor
        if sq == rei_xeque:
            fundo = f"radial-gradient(circle, #ff3b3b 25%, {cor} 80%)"
        elif sq in alvos:
            fundo = (f"radial-gradient(circle, transparent 58%, rgba(0,0,0,.28) 60%) , {cor}"
                     if b.piece_at(sq) else
                     f"radial-gradient(circle, rgba(0,0,0,.28) 16%, transparent 18%), {cor}")
        p = b.piece_at(sq)
        if p and p.color == chess.WHITE:
            texto = "color:#fff !important; text-shadow:0 0 2px #000,0 0 2px #000,0 0 1px #000;"
        else:
            texto = "color:#111 !important; text-shadow:none;"
        regras.append(f".st-key-xq_{sq} button{{background:{fundo} !important;{texto}}}")
    st.markdown("<style>" + "\n".join(regras) + "</style>", unsafe_allow_html=True)


def jogo_xadrez():
    c1, c2, c3 = st.columns(3)
    c1.radio("Jogar de", ["Brancas", "Pretas"], key="xq_lado", horizontal=True,
             help="Vale a partir da próxima partida.")
    c2.radio("Nível", list(NIVEIS_XQ), index=1, key="xq_nivel", horizontal=True)
    c3.selectbox("Promover peão a", list(PROMOCAO), key="xq_promo")

    if "xq_board" not in S:
        xq_novo()
    b = S.xq_board
    fim = b.outcome(claim_draw=True)

    xq_css(b)
    fileiras = range(7, -1, -1) if S.xq_cor == chess.WHITE else range(8)
    colunas = range(8) if S.xq_cor == chess.WHITE else range(7, -1, -1)
    with st.container(key="xq_tab"):
        for r in fileiras:
            cols = st.columns(8)
            for j, f in enumerate(colunas):
                sq = chess.square(f, r)
                p = b.piece_at(sq)
                cols[j].button(SIMBOLO_XQ[p.piece_type] if p else "⠀", key=f"xq_{sq}",
                               on_click=xq_click, args=(sq,), help=chess.square_name(sq))

    # Situação da partida
    if fim:
        if fim.winner is None:
            st.warning(f"🤝 Empate por {FIM_PT.get(fim.termination, 'regra')}.")
        elif fim.winner == S.xq_cor:
            st.success("🏆 Xeque-mate! Você venceu!")
            st.balloons()
        else:
            st.error("🤖 Xeque-mate! O computador venceu.")
    elif b.turn == S.xq_cor:
        st.info(("⚠️ Você está em **xeque**! " if b.is_check() else "") +
                "Sua vez: clique numa peça e depois na casa de destino.")

    b1, b2 = st.columns(2)
    b1.button("↩️ Desfazer lance", key="xq_undo", on_click=xq_desfazer)
    if b2.button("🔄 Nova partida", key="xq_reset"):
        xq_novo()
        st.rerun()

    with st.expander("📜 Lances da partida"):
        st.write(chess.Board().variation_san(b.move_stack) if b.move_stack else "Nenhum lance ainda.")

    # Vez do computador: o tabuleiro já mostra o seu lance enquanto ele pensa
    if not fim and b.turn != S.xq_cor:
        with st.spinner("🤖 Computador pensando..."):
            lance = xq_melhor_lance(b.copy(), S.xq_nivel)
        b.push(lance)
        st.rerun()


def css_grade(chave: str, fonte: str, espaco: str = "3px"):
    """CSS de um tabuleiro de botões que não quebra linha no celular."""
    return f"""
    .st-key-{chave} {{ max-width: 520px; margin: 0 auto; }}
    .st-key-{chave} [data-testid="stVerticalBlock"] {{ gap: {espaco} !important; }}
    .st-key-{chave} [data-testid="stHorizontalBlock"] {{ flex-wrap: nowrap !important; gap: {espaco} !important; }}
    .st-key-{chave} [data-testid="stColumn"], .st-key-{chave} [data-testid="column"] {{
        min-width: 0 !important; width: auto !important; flex: 1 1 0 !important; }}
    .st-key-{chave} .stButton, .st-key-{chave} .stButton > button {{ width: 100% !important; }}
    .st-key-{chave} button {{
        aspect-ratio: 1 / 1; min-height: 0 !important; padding: 0 !important;
        border-radius: 5px !important; line-height: 1 !important; font-weight: 800;
        font-size: {fonte} !important; }}
    .st-key-{chave} button p {{ font-size: inherit !important; line-height: 1 !important; font-weight: inherit; }}
    """


# =====================================================================
# 7) TERMO (adivinhe a palavra de 5 letras)
# =====================================================================
PALAVRAS_TERMO = [
    "AMIGO", "BOLSA", "CARRO", "DENTE", "FESTA", "GENTE", "HOTEL", "JOGOS", "LIVRO", "MUNDO",
    "NOITE", "OUTRO", "PRAIA", "PRATO", "RISCO", "SALTO", "TEMPO", "VERDE", "ZEBRA", "AVIAO",
    "BANCO", "CAMPO", "DISCO", "FORNO", "GARFO", "LIMAO", "MANGA", "NUVEM", "PASTA", "POLVO",
    "RAIVA", "SONHO", "TIGRE", "VIDRO", "BRAVO", "CHUVA", "PEDRA", "PORTA", "LAPIS", "MOLHO",
    "PLANO", "SORTE", "TARDE", "VENTO", "CANTO", "CORPO", "FOLHA", "GRUPO", "LEITE", "NAVIO",
    "PAPEL", "QUEDA", "SABOR", "TRIGO", "VIOLA", "CALOR", "FLUXO", "GOLPE", "JUSTO", "MAGIA",
]
CORES_TERMO = {"verde": "#3aa35b", "amarelo": "#d4a72c", "cinza": "#6b6f76", "vazio": "transparent"}


def sem_acento(txt: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", txt) if unicodedata.category(c) != "Mn")


def termo_cores(chute, alvo):
    res, resto = ["cinza"] * 5, list(alvo)
    for i in range(5):
        if chute[i] == alvo[i]:
            res[i] = "verde"
            resto.remove(chute[i])
    for i in range(5):
        if res[i] != "verde" and chute[i] in resto:
            res[i] = "amarelo"
            resto.remove(chute[i])
    return res


def termo_novo():
    S.termo_alvo = random.choice(PALAVRAS_TERMO)
    S.termo_chutes = []
    S.termo_msg = ""


def termo_html(chutes, alvo):
    linhas = []
    for n in range(6):
        if n < len(chutes):
            letras, cores = chutes[n], termo_cores(chutes[n], alvo)
        else:
            letras, cores = " " * 5, ["vazio"] * 5
        celulas = "".join(
            f"<div style='width:52px;height:52px;display:flex;align-items:center;justify-content:center;"
            f"font-size:1.6rem;font-weight:800;color:#fff;border-radius:6px;background:{CORES_TERMO[c]};"
            f"border:2px solid {'#888' if c == 'vazio' else CORES_TERMO[c]}'>{l}</div>"
            for l, c in zip(letras, cores))
        linhas.append(f"<div style='display:flex;gap:6px;justify-content:center'>{celulas}</div>")
    return "<div style='display:flex;flex-direction:column;gap:6px;margin:8px 0'>" + "".join(linhas) + "</div>"


def jogo_termo():
    if "termo_alvo" not in S:
        termo_novo()
    alvo, chutes = S.termo_alvo, S.termo_chutes
    venceu = bool(chutes) and chutes[-1] == alvo
    perdeu = len(chutes) >= 6 and not venceu

    st.markdown(termo_html(chutes, alvo), unsafe_allow_html=True)

    if venceu:
        st.success(f"🎉 Acertou em {len(chutes)} tentativa(s)!")
        st.balloons()
    elif perdeu:
        st.error(f"😢 Acabaram as tentativas. A palavra era **{alvo}**.")
    else:
        with st.form("termo_form", clear_on_submit=True):
            chute = st.text_input("Sua palavra (5 letras)", max_chars=5)
            if st.form_submit_button("Enviar ✅"):
                chute = sem_acento(chute.strip().upper())
                if len(chute) != 5 or not chute.isalpha():
                    S.termo_msg = "Digite exatamente 5 letras."
                else:
                    S.termo_msg = ""
                    S.termo_chutes.append(chute)
                st.rerun()
        if S.termo_msg:
            st.warning(S.termo_msg)

        # Teclado com as letras já testadas
        estado = {}
        prioridade = {"verde": 3, "amarelo": 2, "cinza": 1}
        for c in chutes:
            for l, cor in zip(c, termo_cores(c, alvo)):
                if prioridade[cor] > prioridade.get(estado.get(l), 0):
                    estado[l] = cor
        teclas = []
        for linha in ("QWERTYUIOP", "ASDFGHJKL", "ZXCVBNM"):
            teclas.append("<div style='display:flex;gap:4px;justify-content:center;margin:3px 0'>" + "".join(
                f"<span style='min-width:26px;padding:6px 4px;text-align:center;border-radius:4px;font-weight:700;"
                f"color:{'#fff' if l in estado else 'inherit'};"
                f"background:{CORES_TERMO[estado[l]] if l in estado else 'rgba(128,128,128,.18)'}'>{l}</span>"
                for l in linha) + "</div>")
        st.markdown("".join(teclas), unsafe_allow_html=True)

    if st.button("🔄 Nova palavra", key="termo_reset"):
        termo_novo()
        st.rerun()


# =====================================================================
# 8) 2048
# =====================================================================
CORES_2048 = {0: ("#cdc1b4", "#776e65"), 2: ("#eee4da", "#776e65"), 4: ("#ede0c8", "#776e65"),
              8: ("#f2b179", "#fff"), 16: ("#f59563", "#fff"), 32: ("#f67c5f", "#fff"),
              64: ("#f65e3b", "#fff"), 128: ("#edcf72", "#fff"), 256: ("#edcc61", "#fff"),
              512: ("#edc850", "#fff"), 1024: ("#edc53f", "#fff"), 2048: ("#edc22e", "#fff")}


def g2048_juntar(linha):
    v = [x for x in linha if x]
    saida, pontos, i = [], 0, 0
    while i < len(v):
        if i + 1 < len(v) and v[i] == v[i + 1]:
            saida.append(v[i] * 2)
            pontos += v[i] * 2
            i += 2
        else:
            saida.append(v[i])
            i += 1
    return saida + [0] * (4 - len(saida)), pontos


def g2048_mover(grade, direcao):
    """Retorna (nova_grade, pontos, mudou)."""
    nova = [[0] * 4 for _ in range(4)]
    pontos = 0
    for k in range(4):
        if direcao == "esq":
            idx = [(k, c) for c in range(4)]
        elif direcao == "dir":
            idx = [(k, c) for c in range(3, -1, -1)]
        elif direcao == "cima":
            idx = [(r, k) for r in range(4)]
        else:
            idx = [(r, k) for r in range(3, -1, -1)]
        linha, p = g2048_juntar([grade[r][c] for r, c in idx])
        pontos += p
        for (r, c), val in zip(idx, linha):
            nova[r][c] = val
    return nova, pontos, nova != grade


def g2048_nova_peca(grade):
    vazias = [(r, c) for r in range(4) for c in range(4) if not grade[r][c]]
    if vazias:
        r, c = random.choice(vazias)
        grade[r][c] = 4 if random.random() < 0.1 else 2


def g2048_novo():
    S.g2048_grade = [[0] * 4 for _ in range(4)]
    g2048_nova_peca(S.g2048_grade)
    g2048_nova_peca(S.g2048_grade)
    S.g2048_pontos = 0
    S.g2048_continuar = False


def g2048_jogar(direcao):
    nova, pontos, mudou = g2048_mover(S.g2048_grade, direcao)
    if mudou:
        g2048_nova_peca(nova)
        S.g2048_grade = nova
        S.g2048_pontos += pontos
        S.g2048_recorde = max(S.get("g2048_recorde", 0), S.g2048_pontos)


def jogo_2048():
    if "g2048_grade" not in S:
        g2048_novo()
    grade = S.g2048_grade
    c1, c2 = st.columns(2)
    c1.metric("Pontos", S.g2048_pontos)
    c2.metric("Recorde", S.get("g2048_recorde", 0))

    celulas = ""
    for linha in grade:
        for v in linha:
            fundo, cor = CORES_2048.get(v, ("#3c3a32", "#fff"))
            tam = "2rem" if v < 100 else "1.6rem" if v < 1000 else "1.3rem"
            celulas += (f"<div style='aspect-ratio:1;display:flex;align-items:center;justify-content:center;"
                        f"border-radius:6px;background:{fundo};color:{cor};font-weight:800;font-size:{tam}'>"
                        f"{v or ''}</div>")
    st.markdown("<div style='display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:8px;"
                "background:#bbada0;border-radius:8px;max-width:380px;margin:0 auto 12px'>"
                + celulas + "</div>", unsafe_allow_html=True)

    tem_2048 = any(v >= 2048 for linha in grade for v in linha)
    sem_lances = not any(g2048_mover(grade, d)[2] for d in ("esq", "dir", "cima", "baixo"))
    if tem_2048 and not S.g2048_continuar:
        st.success("🏆 Você fez 2048! Pode continuar jogando para aumentar os pontos.")
        if st.button("Continuar jogando", key="g2048_cont"):
            S.g2048_continuar = True
            st.rerun()
    if sem_lances:
        st.error(f"Fim de jogo! Você fez {S.g2048_pontos} pontos.")
    else:
        css_botoes(56, 1.5)
        _, cima, _ = st.columns(3)
        cima.button("⬆️", key="g2048_cima", on_click=g2048_jogar, args=("cima",))
        esq, baixo, dir_ = st.columns(3)
        esq.button("⬅️", key="g2048_esq", on_click=g2048_jogar, args=("esq",))
        baixo.button("⬇️", key="g2048_baixo", on_click=g2048_jogar, args=("baixo",))
        dir_.button("➡️", key="g2048_dir", on_click=g2048_jogar, args=("dir",))

    if st.button("🔄 Novo jogo", key="g2048_reset"):
        g2048_novo()
        st.rerun()


# =====================================================================
# 9) CAMPO MINADO
# =====================================================================
CM_TAM = {"Fácil (8×8, 10 minas)": (8, 10), "Médio (10×10, 18 minas)": (10, 18)}
CORES_NUM = {1: "#1e63d6", 2: "#2e8b3a", 3: "#d32f2f", 4: "#283593",
             5: "#8d1c1c", 6: "#00838f", 7: "#222", 8: "#666"}


def cm_vizinhos(i, n):
    r, c = divmod(i, n)
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if (dr or dc) and 0 <= r + dr < n and 0 <= c + dc < n:
                yield (r + dr) * n + c + dc


def cm_novo():
    S.cm_n, S.cm_qtd = CM_TAM[S.get("cm_nivel", list(CM_TAM)[0])]
    S.cm_minas = None
    S.cm_abertas = set()
    S.cm_bandeiras = set()
    S.cm_fim = None
    S.cm_explodiu = None


def cm_numero(i):
    return sum(j in S.cm_minas for j in cm_vizinhos(i, S.cm_n))


def cm_click(i):
    if S.cm_fim or i in S.cm_abertas:
        return
    if S.cm_modo == "🚩 Bandeira":
        S.cm_bandeiras.symmetric_difference_update({i})
        return
    if i in S.cm_bandeiras:
        return
    n = S.cm_n
    if S.cm_minas is None:  # 1º clique nunca é mina
        proibidas = {i, *cm_vizinhos(i, n)}
        S.cm_minas = set(random.sample([j for j in range(n * n) if j not in proibidas], S.cm_qtd))
    if i in S.cm_minas:
        S.cm_fim, S.cm_explodiu = "perdeu", i
        return
    pilha = [i]
    while pilha:
        j = pilha.pop()
        if j in S.cm_abertas:
            continue
        S.cm_abertas.add(j)
        S.cm_bandeiras.discard(j)
        if cm_numero(j) == 0:
            pilha.extend(k for k in cm_vizinhos(j, n) if k not in S.cm_abertas)
    if len(S.cm_abertas) == n * n - S.cm_qtd:
        S.cm_fim = "venceu"


def jogo_campo_minado():
    c1, c2 = st.columns(2)
    c1.radio("Tamanho", list(CM_TAM), key="cm_nivel", help="Vale a partir do próximo jogo.")
    c2.radio("Ao clicar:", ["⛏️ Abrir", "🚩 Bandeira"], key="cm_modo", horizontal=True)
    if "cm_abertas" not in S:
        cm_novo()
    n = S.cm_n
    st.write(f"💣 Minas: **{S.cm_qtd}** · 🚩 Bandeiras: **{len(S.cm_bandeiras)}**")

    regras = [css_grade("cm_tab", "clamp(.9rem, 4vw, 1.4rem)", "2px")]
    for i in range(n * n):
        if i in S.cm_abertas:
            num = cm_numero(i)
            estilo = f"background:#e9e9e9 !important; color:{CORES_NUM.get(num, '#222')} !important; border:1px solid #cfcfcf !important;"
        elif i == S.cm_explodiu:
            estilo = "background:#ff5252 !important; border:none !important;"
        else:
            estilo = "background:#8fa3b8 !important; color:#fff !important; border:2px outset #b9c8d8 !important;"
        regras.append(f".st-key-cm_{i} button{{{estilo}}}")
    st.markdown("<style>" + "\n".join(regras) + "</style>", unsafe_allow_html=True)

    with st.container(key="cm_tab"):
        for r in range(n):
            cols = st.columns(n)
            for c in range(n):
                i = r * n + c
                if i in S.cm_abertas:
                    num = cm_numero(i)
                    rotulo = str(num) if num else "⠀"
                elif S.cm_fim and S.cm_minas and i in S.cm_minas:
                    rotulo = "💣"
                elif i in S.cm_bandeiras:
                    rotulo = "🚩"
                else:
                    rotulo = "⠀"
                cols[c].button(rotulo, key=f"cm_{i}", on_click=cm_click, args=(i,))

    if S.cm_fim == "venceu":
        st.success("🎉 Você limpou o campo!")
        st.balloons()
    elif S.cm_fim == "perdeu":
        st.error("💥 Boom! Você pisou numa mina.")

    if st.button("🔄 Novo campo", key="cm_reset"):
        cm_novo()
        st.rerun()


# =====================================================================
# 10) LIGUE 4 (contra o computador)
# =====================================================================
L4_LIN, L4_COL = 6, 7


def l4_vence(t, p):
    for r in range(L4_LIN):
        for c in range(L4_COL):
            for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
                if all(0 <= r + k * dr < L4_LIN and 0 <= c + k * dc < L4_COL
                       and t[r + k * dr][c + k * dc] == p for k in range(4)):
                    return True
    return False


def l4_validas(t):
    return [c for c in range(L4_COL) if not t[0][c]]


def l4_soltar(t, c, p):
    for r in range(L4_LIN - 1, -1, -1):
        if not t[r][c]:
            t[r][c] = p
            return r
    return None


def l4_simular(t, c, p):
    novo = [linha[:] for linha in t]
    l4_soltar(novo, c, p)
    return novo


def l4_jogada_pc(t):
    validas = l4_validas(t)
    for p in ("O", "X"):  # 1º tenta vencer, depois bloqueia
        for c in validas:
            if l4_vence(l4_simular(t, c, p), p):
                return c
    seguras = [c for c in validas
               if not any(l4_vence(l4_simular(l4_simular(t, c, "O"), c2, "X"), "X")
                          for c2 in l4_validas(l4_simular(t, c, "O")))]
    opcoes = seguras or validas
    return min(opcoes, key=lambda c: abs(3 - c) + random.random() * 1.8)


def l4_novo():
    S.l4_tab = [[""] * L4_COL for _ in range(L4_LIN)]
    S.l4_fim = None


def l4_click(c):
    t = S.l4_tab
    if S.l4_fim or c not in l4_validas(t):
        return
    l4_soltar(t, c, "X")
    if l4_vence(t, "X"):
        S.l4_fim = "X"
    elif not l4_validas(t):
        S.l4_fim = "Empate"
    else:
        l4_soltar(t, l4_jogada_pc(t), "O")
        if l4_vence(t, "O"):
            S.l4_fim = "O"
        elif not l4_validas(t):
            S.l4_fim = "Empate"
    if S.l4_fim:
        chave = {"X": "voce", "O": "pc", "Empate": "empate"}[S.l4_fim]
        S.l4_placar[chave] += 1


def jogo_ligue4():
    if "l4_tab" not in S:
        l4_novo()
        S.l4_placar = {"voce": 0, "pc": 0, "empate": 0}
    p = S.l4_placar
    c1, c2, c3 = st.columns(3)
    c1.metric("Você (🔴)", p["voce"])
    c2.metric("Empates", p["empate"])
    c3.metric("Computador (🟡)", p["pc"])

    st.markdown("<style>" + css_grade("l4_tab", "clamp(1.2rem, 5.5vw, 2.2rem)", "4px") +
                ".st-key-l4_tab{background:#1f4fbf;padding:8px;border-radius:10px}"
                ".st-key-l4_tab button{background:#163a8f !important;border:none !important;"
                "border-radius:50% !important;}</style>", unsafe_allow_html=True)
    peca = {"X": "🔴", "O": "🟡", "": "⠀"}
    with st.container(key="l4_tab"):
        for r in range(L4_LIN):
            cols = st.columns(L4_COL)
            for c in range(L4_COL):
                cols[c].button(peca[S.l4_tab[r][c]], key=f"l4_{r}_{c}", on_click=l4_click, args=(c,))

    fim = S.l4_fim
    if fim == "X":
        st.success("🎉 Você ligou 4!")
    elif fim == "O":
        st.error("🤖 O computador ligou 4!")
    elif fim == "Empate":
        st.warning("🤝 Tabuleiro cheio, empate!")
    else:
        st.caption("Clique em qualquer casa de uma coluna para soltar sua peça nela.")

    if st.button("🔄 Nova partida", key="l4_reset"):
        l4_novo()
        st.rerun()


# =====================================================================
# 11) QUIZ COM IA (usa a chave Groq)
# =====================================================================
def groq_chat(mensagens, json_mode=False):
    corpo = {"model": S.groq_modelo, "messages": mensagens, "temperature": 0.9}
    if json_mode:
        corpo["response_format"] = {"type": "json_object"}
    r = requests.post("https://api.groq.com/openai/v1/chat/completions",
                      headers={"Authorization": f"Bearer {S.groq_key}"}, json=corpo, timeout=90)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def quiz_gerar(tema, nivel, qtd):
    prompt = (
        f"Crie um quiz em português do Brasil com {qtd} perguntas de múltipla escolha sobre o tema: "
        f"\"{tema}\". Nível de dificuldade: {nivel}. Cada pergunta deve ter exatamente 4 opções e "
        "apenas uma correta. Varie a posição da resposta correta. Responda SOMENTE com JSON no formato: "
        '{"perguntas": [{"pergunta": "...", "opcoes": ["...", "...", "...", "..."], '
        '"correta": 0, "explicacao": "..."}]} onde "correta" é o índice (0 a 3) da opção certa.'
    )
    texto = groq_chat([{"role": "system", "content": "Você cria quizzes educativos, corretos e divertidos."},
                       {"role": "user", "content": prompt}], json_mode=True)
    dados = json.loads(texto)
    perguntas = []
    for q in dados.get("perguntas", []):
        ops = q.get("opcoes", [])
        if (isinstance(ops, list) and len(ops) == 4 and isinstance(q.get("correta"), int)
                and 0 <= q["correta"] < 4 and q.get("pergunta")):
            perguntas.append(q)
    return perguntas


def jogo_quiz_ia():
    if not S.get("quiz_perguntas"):
        st.write("A IA cria um quiz novinho sobre **qualquer tema** que você escolher.")
        with st.form("quiz_form"):
            tema = st.text_input("Tema do quiz", placeholder="Ex.: Copa do Mundo, dinossauros, Brasil Colônia, Harry Potter...")
            c1, c2 = st.columns(2)
            nivel = c1.select_slider("Dificuldade", ["Fácil", "Médio", "Difícil"], value="Médio")
            qtd = c2.select_slider("Perguntas", [5, 10, 15], value=5)
            if st.form_submit_button("✨ Gerar quiz", type="primary"):
                if not tema.strip():
                    st.error("Escreva um tema.")
                else:
                    with st.spinner("A IA está preparando as perguntas..."):
                        try:
                            perguntas = quiz_gerar(tema.strip(), nivel, qtd)
                        except requests.HTTPError as e:
                            perguntas = None
                            st.error(f"A Groq recusou o pedido (erro {e.response.status_code}). Tente de novo.")
                        except (requests.RequestException, ValueError, KeyError):
                            perguntas = None
                            st.error("Não consegui gerar o quiz agora. Tente de novo.")
                    if perguntas:
                        S.quiz_perguntas, S.quiz_tema = perguntas, tema.strip()
                        S.quiz_i, S.quiz_pontos, S.quiz_respondida = 0, 0, None
                        st.rerun()
                    elif perguntas is not None:
                        st.error("A IA não mandou perguntas válidas. Tente de novo ou mude o tema.")
        return

    perguntas, i = S.quiz_perguntas, S.quiz_i
    if i >= len(perguntas):
        total = len(perguntas)
        st.subheader(f"Resultado: {S.quiz_pontos} de {total} 🎯")
        st.progress(S.quiz_pontos / total)
        if S.quiz_pontos == total:
            st.balloons()
            st.success("Gabaritou! 🏆")
        elif S.quiz_pontos >= total * 0.6:
            st.success("Mandou bem! 👏")
        else:
            st.info("Dá para melhorar, tente outro! 💪")
        if st.button("✨ Novo quiz", key="quiz_novo"):
            S.quiz_perguntas = None
            st.rerun()
        return

    q = perguntas[i]
    st.caption(f"Tema: {S.quiz_tema} · Pergunta {i + 1} de {len(perguntas)} · Pontos: {S.quiz_pontos}")
    st.progress(i / len(perguntas))
    st.subheader(q["pergunta"])
    escolha = st.radio("Escolha uma opção", q["opcoes"], index=None, key=f"quiz_r_{i}",
                       disabled=S.quiz_respondida is not None, label_visibility="collapsed")

    if S.quiz_respondida is None:
        if st.button("Responder ✅", key=f"quiz_ok_{i}", disabled=escolha is None):
            S.quiz_respondida = q["opcoes"].index(escolha)
            if S.quiz_respondida == q["correta"]:
                S.quiz_pontos += 1
            st.rerun()
    else:
        certa = q["opcoes"][q["correta"]]
        if S.quiz_respondida == q["correta"]:
            st.success("✅ Certa resposta!")
        else:
            st.error(f"❌ Errou. A resposta certa era: **{certa}**")
        if q.get("explicacao"):
            st.info(q["explicacao"])
        if st.button("Próxima ➡️", key=f"quiz_prox_{i}"):
            S.quiz_i += 1
            S.quiz_respondida = None
            st.rerun()

    if st.button("🛑 Encerrar quiz", key="quiz_sair"):
        S.quiz_perguntas = None
        st.rerun()


# =====================================================================
# JOGOS ANIMADOS (HTML5 canvas embutido)
# =====================================================================
BASE_JS = r"""
const cv = document.getElementById('c'), ctx = cv.getContext('2d');
const keys = {};
const MAPA = {ArrowLeft:'esq', KeyA:'esq', KeyZ:'esq', ArrowRight:'dir', KeyD:'dir', KeyM:'dir', Slash:'dir',
              ArrowUp:'cima', KeyW:'cima', ArrowDown:'baixo', KeyS:'baixo', Space:'acao', Enter:'acao', KeyP:'pausa'};
function apertar(k){ if (!keys[k]) { keys[k] = true; aoApertar(k); } }
function soltar(k){ if (keys[k]) { keys[k] = false; aoSoltar(k); } }
addEventListener('keydown', e => { const k = MAPA[e.code]; if (k) { e.preventDefault(); apertar(k); } });
addEventListener('keyup', e => { const k = MAPA[e.code]; if (k) { e.preventDefault(); soltar(k); } });
document.querySelectorAll('[data-k]').forEach(b => {
  const k = b.dataset.k;
  b.addEventListener('pointerdown', e => { e.preventDefault(); b.setPointerCapture(e.pointerId); apertar(k); });
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(t => b.addEventListener(t, e => { e.preventDefault(); soltar(k); }));
  b.addEventListener('contextmenu', e => e.preventDefault());
});
function lerRecorde(n){ try { return +localStorage.getItem(n) || 0; } catch (e) { return 0; } }
function salvarRecorde(n, v){ const r = lerRecorde(n); if (v > r) { try { localStorage.setItem(n, v); } catch (e) {} return v; } return r; }
function texto(t, x, y, tam, cor, alinh){ ctx.font = `bold ${tam}px system-ui, sans-serif`; ctx.fillStyle = cor || '#fff';
  ctx.textAlign = alinh || 'center'; ctx.textBaseline = 'middle'; ctx.fillText(t, x, y); }
function painel(titulo, linhas){ ctx.fillStyle = 'rgba(5,8,20,.72)'; ctx.fillRect(0, 0, cv.width, cv.height);
  texto(titulo, cv.width/2, cv.height/2 - 30 - linhas.length*12, 34, '#ffd34d');
  linhas.forEach((l, i) => texto(l, cv.width/2, cv.height/2 + 10 + i*28 - linhas.length*12, 17, '#fff')); }
function rr(x, y, w, h, r){ ctx.beginPath(); ctx.moveTo(x+r, y); ctx.arcTo(x+w, y, x+w, y+h, r); ctx.arcTo(x+w, y+h, x, y+h, r);
  ctx.arcTo(x, y+h, x, y, r); ctx.arcTo(x, y, x+w, y, r); ctx.closePath(); }
function ajudaInicio(){ return matchMedia('(pointer: coarse)').matches ? 'Toque na tela para começar' : 'Clique aqui e aperte ESPAÇO'; }
let ultimoT = performance.now();
function loop(t){ const dt = Math.min(0.04, (t - ultimoT) / 1000); ultimoT = t; atualizar(dt); desenhar(); requestAnimationFrame(loop); }
"""


def pagina_canvas(js_jogo: str, largura: int, botoes: str) -> str:
    return f"""<!doctype html><html><head><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
html,body{{margin:0;background:transparent;font-family:system-ui,sans-serif;user-select:none;-webkit-user-select:none;
  -webkit-touch-callout:none;overflow:hidden}}
#wrap{{display:flex;flex-direction:column;align-items:center;gap:10px;padding:4px}}
canvas{{width:min(100%,{largura}px);height:auto;border-radius:14px;box-shadow:0 8px 28px rgba(0,0,0,.4);
  touch-action:none;display:block;outline:none}}
.ctl{{display:flex;gap:8px;width:min(100%,{largura}px)}}
.ctl button{{flex:1;padding:14px 0;font-size:20px;font-weight:700;border:none;border-radius:12px;background:#283044;
  color:#fff;touch-action:none;cursor:pointer}}
.ctl button:active{{background:#46526e;transform:translateY(1px)}}
</style></head><body><div id="wrap"><canvas id="c" tabindex="0"></canvas><div class="ctl">{botoes}</div></div>
<script>{BASE_JS}
{js_jogo}
requestAnimationFrame(loop);
</script></body></html>"""


# ---------------------------------------------------------------- CORRIDA
CORRIDA_JS = r"""
const W = 360, H = 600; cv.width = W; cv.height = H;
const RX = 50, RW = 260;                       // estrada
const CORES = ['#3d8bff', '#ffb02e', '#a259ff', '#2ec4b6', '#f2f2f2', '#ff6fb5'];
let estado = 'inicio', carro, inimigos, moedas, part, arvores, vel, pontos, vidas, invul, spawnT, moedaT, faixa, recorde = lerRecorde('rec_corrida');
function reiniciar(){
  carro = {x: W/2, y: H - 95, w: 36, h: 62}; inimigos = []; moedas = []; part = [];
  vel = 280; pontos = 0; vidas = 3; invul = 0; spawnT = 1; moedaT = 2; faixa = 0;
  arvores = []; for (let i = 0; i < 10; i++) arvores.push({x: i % 2 ? RX + RW + 12 + Math.random()*24 : 8 + Math.random()*26, y: i * 65, r: 12 + Math.random()*7});
}
reiniciar();
function aoApertar(k){
  if (k === 'acao') { if (estado === 'inicio' || estado === 'fim') { reiniciar(); estado = 'jogando'; } else if (estado === 'pausa') estado = 'jogando'; }
  if (k === 'pausa') estado = estado === 'jogando' ? 'pausa' : estado === 'pausa' ? 'jogando' : estado;
}
function aoSoltar(k){}
const toques = {};
cv.addEventListener('pointerdown', e => {
  cv.focus();
  if (estado !== 'jogando') { aoApertar('acao'); return; }
  const r = cv.getBoundingClientRect(); const lado = (e.clientX - r.left) < r.width/2 ? 'esq' : 'dir';
  toques[e.pointerId] = lado; keys[lado] = true;
});
['pointerup', 'pointercancel', 'pointerleave'].forEach(t => cv.addEventListener(t, e => {
  const l = toques[e.pointerId]; if (l) { delete toques[e.pointerId]; if (!Object.values(toques).includes(l)) keys[l] = false; }
}));
function bate(a, b){ return Math.abs(a.x - b.x) < (a.w + b.w)/2 - 5 && Math.abs(a.y - b.y) < (a.h + b.h)/2 - 6; }
function explodir(x, y, cor, n){ for (let i = 0; i < n; i++) { const a = Math.random()*6.28, s = 60 + Math.random()*260;
  part.push({x, y, vx: Math.cos(a)*s, vy: Math.sin(a)*s, t: 0.6 + Math.random()*0.5, cor}); } }
function atualizar(dt){
  for (const p of part) { p.x += p.vx*dt; p.y += p.vy*dt; p.t -= dt; }
  part = part.filter(p => p.t > 0);
  if (estado !== 'jogando') return;
  vel = Math.min(760, vel + dt*8);
  pontos += vel*dt/10; faixa = (faixa + vel*dt) % 60;
  for (const a of arvores) { a.y += vel*dt; if (a.y > H + 30) a.y -= 650; }
  const lateral = 300 + vel*0.15;
  if (keys.esq) carro.x -= lateral*dt;
  if (keys.dir) carro.x += lateral*dt;
  carro.x = Math.max(RX + carro.w/2 + 4, Math.min(RX + RW - carro.w/2 - 4, carro.x));
  spawnT -= dt;
  if (spawnT <= 0) {
    spawnT = Math.max(0.38, 1.15 - vel/900) + Math.random()*0.45;
    const f = Math.floor(Math.random()*3), x = RX + RW/6*(1 + 2*f);
    if (!inimigos.some(e => Math.abs(e.x - x) < 5 && e.y < 90))
      inimigos.push({x, y: -70, w: 36, h: 62, v: vel*(0.3 + Math.random()*0.3), cor: CORES[Math.floor(Math.random()*CORES.length)]});
  }
  moedaT -= dt;
  if (moedaT <= 0) { moedaT = 1.2 + Math.random()*1.8; const f = Math.floor(Math.random()*3);
    moedas.push({x: RX + RW/6*(1 + 2*f), y: -30, w: 22, h: 22, giro: 0}); }
  for (const e of inimigos) e.y += (vel - e.v)*dt;
  for (const m of moedas) { m.y += vel*dt; m.giro += dt*6; }
  invul = Math.max(0, invul - dt);
  for (const e of inimigos) if (!e.morto && invul <= 0 && bate(carro, e)) {
    e.morto = true; vidas--; invul = 2; explodir((carro.x + e.x)/2, (carro.y + e.y)/2, '#ff8a3d', 40); vel *= 0.7;
    if (vidas <= 0) { estado = 'fim'; recorde = salvarRecorde('rec_corrida', Math.floor(pontos)); }
  }
  for (const m of moedas) if (!m.pega && bate(carro, m)) { m.pega = true; pontos += 50; explodir(m.x, m.y, '#ffe066', 12); }
  inimigos = inimigos.filter(e => !e.morto && e.y < H + 80);
  moedas = moedas.filter(m => !m.pega && m.y < H + 40);
}
function desenhaCarro(x, y, w, h, cor, jogador){
  ctx.save(); ctx.translate(x, y);
  ctx.fillStyle = '#111'; [[-w/2-4, -h/2+8], [w/2-3, -h/2+8], [-w/2-4, h/2-20], [w/2-3, h/2-20]].forEach(([a, b]) => { rr(a, b, 7, 14, 3); ctx.fill(); });
  ctx.fillStyle = cor; rr(-w/2, -h/2, w, h, 9); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.25)'; rr(-w/2 + 4, -h/2 + 3, w - 8, 6, 3); ctx.fill();
  ctx.fillStyle = '#1b2433'; rr(-w/2 + 5, jogador ? -h/2 + 14 : h/2 - 26, w - 10, 12, 4); ctx.fill();
  rr(-w/2 + 6, jogador ? h/2 - 20 : -h/2 + 12, w - 12, 8, 3); ctx.fill();
  if (jogador) { ctx.fillStyle = '#fff'; ctx.fillRect(-3, -h/2 + 28, 6, 22); }
  ctx.fillStyle = jogador ? '#fff7b0' : '#ff4d4d';
  ctx.fillRect(-w/2 + 4, jogador ? -h/2 : h/2 - 4, 8, 4); ctx.fillRect(w/2 - 12, jogador ? -h/2 : h/2 - 4, 8, 4);
  ctx.restore();
}
function desenhar(){
  ctx.fillStyle = '#2f8f3a'; ctx.fillRect(0, 0, W, H);
  for (const a of arvores) { ctx.fillStyle = '#1f6b2b'; ctx.beginPath(); ctx.arc(a.x + 3, a.y + 3, a.r, 0, 7); ctx.fill();
    ctx.fillStyle = '#3fae4f'; ctx.beginPath(); ctx.arc(a.x, a.y, a.r, 0, 7); ctx.fill(); }
  ctx.fillStyle = '#3a3d46'; ctx.fillRect(RX, 0, RW, H);
  for (let y = -40 + faixa % 40; y < H; y += 40) {
    ctx.fillStyle = (Math.floor((y - faixa)/40) % 2) ? '#e53935' : '#fff';
    ctx.fillRect(RX - 8, y, 8, 20); ctx.fillRect(RX + RW, y, 8, 20);
    ctx.fillStyle = (Math.floor((y - faixa)/40) % 2) ? '#fff' : '#e53935';
    ctx.fillRect(RX - 8, y + 20, 8, 20); ctx.fillRect(RX + RW, y + 20, 8, 20);
  }
  ctx.fillStyle = 'rgba(255,255,255,.75)';
  for (let y = -60 + faixa; y < H; y += 60) { ctx.fillRect(RX + RW/3 - 3, y, 6, 30); ctx.fillRect(RX + 2*RW/3 - 3, y, 6, 30); }
  for (const m of moedas) { const s = Math.abs(Math.cos(m.giro));
    ctx.fillStyle = '#f5b700'; ctx.beginPath(); ctx.ellipse(m.x, m.y, 11*s + 1, 11, 0, 0, 7); ctx.fill();
    ctx.fillStyle = '#ffe066'; ctx.beginPath(); ctx.ellipse(m.x, m.y, 7*s + 0.5, 7, 0, 0, 7); ctx.fill(); }
  for (const e of inimigos) desenhaCarro(e.x, e.y, e.w, e.h, e.cor, false);
  if (estado !== 'fim' && !(invul > 0 && Math.floor(invul*10) % 2)) desenhaCarro(carro.x, carro.y, carro.w, carro.h, '#e53935', true);
  for (const p of part) { ctx.globalAlpha = Math.max(0, p.t); ctx.fillStyle = p.cor; ctx.fillRect(p.x - 3, p.y - 3, 6, 6); }
  ctx.globalAlpha = 1;
  ctx.fillStyle = 'rgba(0,0,0,.45)'; rr(8, 8, 150, 52, 10); ctx.fill(); rr(W - 118, 8, 110, 52, 10); ctx.fill();
  texto('🏁 ' + Math.floor(pontos), 18, 24, 18, '#fff', 'left');
  texto(Math.round(vel/3) + ' km/h', 18, 46, 14, '#9fe6ff', 'left');
  texto('❤️'.repeat(Math.max(0, vidas)), W - 63, 24, 16);
  texto('Recorde ' + recorde, W - 63, 46, 13, '#ffd34d');
  if (estado === 'inicio') painel('🏎️ Corrida', ['Desvie dos carros e pegue as moedas!', '← → ou toque nos lados da tela', ajudaInicio()]);
  if (estado === 'pausa') painel('⏸️ Pausado', ['ESPAÇO ou toque para continuar']);
  if (estado === 'fim') painel('💥 Fim de corrida!', ['Pontos: ' + Math.floor(pontos), 'Recorde: ' + recorde, 'ESPAÇO ou toque para jogar de novo']);
}
"""

# ---------------------------------------------------------------- COME-COME
COMECOME_JS = r"""
const MAPA_TXT = [
 '###################',
 '#........#........#',
 '#o##.###.#.###.##o#',
 '#.................#',
 '#.##.#.#####.#.##.#',
 '#....#...#...#....#',
 '####.###.#.###.####',
 '####.#.......#.####',
 '####.#.##-##.#.####',
 '.......#EEE#.......',
 '####.#.#####.#.####',
 '####.#.......#.####',
 '####.#.#####.#.####',
 '#........#........#',
 '#.##.###.#.###.##.#',
 '#o.#.....P.....#.o#',
 '##.#.#.#####.#.#.##',
 '#....#...#...#....#',
 '#.######.#.######.#',
 '#.................#',
 '###################'];
const C = 19, L = 21, T = 24, TOPO = 34;
cv.width = C*T; cv.height = L*T + TOPO;
const DIRS = {esq: [-1, 0], dir: [1, 0], cima: [0, -1], baixo: [0, 1]};
const CORES_INI = ['#ff4d6d', '#ff9f1c', '#c77dff'];
let grade, resta, jog, inis, estado = 'inicio', pontos = 0, vidas = 3, nivel = 1, poderT = 0, combo = 0, timer = 0, relogio = 0,
    flutuantes = [], recorde = lerRecorde('rec_come');
function carregarMapa(){ grade = MAPA_TXT.map(l => l.replace(/[PE]/g, ' ').split('')); resta = 0;
  grade.forEach(l => l.forEach(c => { if (c === '.' || c === 'o') resta++; })); }
function posicionar(){
  jog = {x: 9, y: 15, dx: 0, dy: 0, p: 0, q: null, vel: Math.min(8.2, 6.6 + nivel*0.2)};
  const vi = Math.min(7.6, 5.0 + nivel*0.4);
  inis = [{x: 9, y: 7, modo: 'caca', espera: 0}, {x: 8, y: 9, modo: 'casa', espera: 2.5}, {x: 10, y: 9, modo: 'casa', espera: 6}]
    .map((e, i) => Object.assign(e, {dx: 0, dy: 0, p: 0, vel: vi, tipo: i, cor: CORES_INI[i]}));
  inis[0].dx = -1; poderT = 0;
}
function novoJogo(){ pontos = 0; vidas = 3; nivel = 1; carregarMapa(); posicionar(); }
novoJogo();
function celula(x, y){ x = ((x % C) + C) % C; if (y < 0 || y >= L) return '#'; return grade[y][x]; }
function passa(x, y, e){ const c = celula(x, y); if (c === '#') return false;
  if (c === '-') return !!e && (e.modo === 'saindo' || e.modo === 'voltando'); return true; }
function enrolar(e){ e.x = ((e.x % C) + C) % C; }
function aoApertar(k){
  if (DIRS[k] && jog) jog.q = DIRS[k];
  if (k === 'acao') { if (estado === 'inicio' || estado === 'fim') { novoJogo(); estado = 'pronto'; timer = 1.2; } else if (estado === 'pausa') estado = 'jogando'; }
  if (k === 'pausa') estado = estado === 'jogando' ? 'pausa' : estado === 'pausa' ? 'jogando' : estado;
}
function aoSoltar(k){}
let toqueIni = null;
cv.addEventListener('pointerdown', e => { cv.focus(); if (estado === 'inicio' || estado === 'fim' || estado === 'pausa') { aoApertar('acao'); return; }
  toqueIni = {x: e.clientX, y: e.clientY}; });
cv.addEventListener('pointermove', e => { if (!toqueIni) return; const dx = e.clientX - toqueIni.x, dy = e.clientY - toqueIni.y;
  if (Math.hypot(dx, dy) > 18) { jog.q = Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? DIRS.dir : DIRS.esq) : (dy > 0 ? DIRS.baixo : DIRS.cima); toqueIni = {x: e.clientX, y: e.clientY}; } });
['pointerup', 'pointercancel'].forEach(t => cv.addEventListener(t, () => toqueIni = null));
function comer(x, y){
  const c = grade[y][x];
  if (c === '.') { grade[y][x] = ' '; pontos += 10; resta--; }
  else if (c === 'o') { grade[y][x] = ' '; pontos += 50; resta--; poderT = Math.max(3, 8 - nivel*0.6); combo = 0;
    for (const e of inis) if (e.modo === 'caca') { e.modo = 'medo'; if (e.dx || e.dy) { e.x += e.dx; e.y += e.dy; enrolar(e); e.dx = -e.dx; e.dy = -e.dy; e.p = 1 - e.p; } } }
  if (resta === 0) { estado = 'nivel'; timer = 2; }
}
function moverJog(dt){
  const j = jog;
  if (j.q && (j.dx || j.dy) && j.q[0] === -j.dx && j.q[1] === -j.dy) { j.x += j.dx; j.y += j.dy; enrolar(j); j.dx = -j.dx; j.dy = -j.dy; j.p = 1 - j.p; }
  if (!j.dx && !j.dy) { if (j.q && passa(j.x + j.q[0], j.y + j.q[1])) { j.dx = j.q[0]; j.dy = j.q[1]; } else return; }
  j.p += j.vel*dt;
  while (j.p >= 1) {
    j.p -= 1; j.x += j.dx; j.y += j.dy; enrolar(j); comer(j.x, j.y);
    if (j.q && passa(j.x + j.q[0], j.y + j.q[1])) { j.dx = j.q[0]; j.dy = j.q[1]; }
    else if (!passa(j.x + j.dx, j.y + j.dy)) { j.dx = 0; j.dy = 0; j.p = 0; break; }
  }
}
function alvo(e){
  if (e.modo === 'saindo') return [9, 7];
  if (e.modo === 'voltando') return [9, 9];
  if (e.modo === 'medo') return null;
  if (e.tipo === 0) return [jog.x, jog.y];
  if (e.tipo === 1) return [jog.x + jog.dx*4, jog.y + jog.dy*4];
  return Math.hypot(e.x - jog.x, e.y - jog.y) > 7 ? [jog.x, jog.y] : [1, 19];
}
function escolherDir(e){
  const opc = [];
  for (const [dx, dy] of Object.values(DIRS)) {
    if ((e.dx || e.dy) && dx === -e.dx && dy === -e.dy) continue;
    if (passa(e.x + dx, e.y + dy, e)) opc.push([dx, dy]);
  }
  if (!opc.length) { e.dx = -e.dx; e.dy = -e.dy; return; }
  const a = alvo(e); let esc;
  if (e.modo === 'medo') {
    esc = Math.random() < 0.35 ? opc[Math.floor(Math.random()*opc.length)]
        : opc.reduce((m, o) => { const d = Math.hypot(e.x + o[0] - jog.x, e.y + o[1] - jog.y); return d > m.d ? {o, d} : m; }, {o: opc[0], d: -1}).o;
  } else if (e.modo === 'caca' && Math.random() < 0.1) esc = opc[Math.floor(Math.random()*opc.length)];
  else esc = opc.reduce((m, o) => { const d = Math.hypot(e.x + o[0] - a[0], e.y + o[1] - a[1]); return d < m.d ? {o, d} : m; }, {o: opc[0], d: 1e9}).o;
  e.dx = esc[0]; e.dy = esc[1];
}
function moverIni(e, dt){
  if (e.modo === 'casa') { e.espera -= dt; if (e.espera <= 0) { e.modo = 'saindo'; escolherDir(e); } return; }
  const v = e.modo === 'medo' ? 3.4 : e.modo === 'voltando' ? 13 : e.modo === 'saindo' ? 4 : e.vel;
  if (!e.dx && !e.dy) escolherDir(e);
  e.p += v*dt;
  while (e.p >= 1) {
    e.p -= 1; e.x += e.dx; e.y += e.dy; enrolar(e);
    if (e.modo === 'saindo' && e.x === 9 && e.y === 7) e.modo = 'caca';
    if (e.modo === 'voltando' && e.x === 9 && e.y === 9) e.modo = 'saindo';
    escolherDir(e);
  }
}
function pos(e){ return [e.x + e.dx*e.p, e.y + e.dy*e.p]; }
function atualizar(dt){
  relogio += dt;
  flutuantes.forEach(f => { f.t -= dt; f.y -= 20*dt; }); flutuantes = flutuantes.filter(f => f.t > 0);
  if (estado === 'pronto') { timer -= dt; if (timer <= 0) estado = 'jogando'; return; }
  if (estado === 'morte') { timer -= dt; if (timer <= 0) { if (vidas > 0) { posicionar(); estado = 'pronto'; timer = 1.2; }
    else { estado = 'fim'; recorde = salvarRecorde('rec_come', pontos); } } return; }
  if (estado === 'nivel') { timer -= dt; if (timer <= 0) { nivel++; carregarMapa(); posicionar(); estado = 'pronto'; timer = 1.5; } return; }
  if (estado !== 'jogando') return;
  for (const k of ['esq', 'dir', 'cima', 'baixo']) if (keys[k]) jog.q = DIRS[k];
  if (poderT > 0) { poderT -= dt; if (poderT <= 0) inis.forEach(e => { if (e.modo === 'medo') e.modo = 'caca'; }); }
  moverJog(dt);
  if (estado !== 'jogando') return;
  for (const e of inis) moverIni(e, dt);
  const [jx, jy] = pos(jog);
  for (const e of inis) {
    const [ex, ey] = pos(e);
    if (Math.hypot(jx - ex, jy - ey) < 0.7) {
      if (e.modo === 'medo') { const pts = 200 * 2 ** combo; combo = Math.min(combo + 1, 3); pontos += pts;
        flutuantes.push({x: ex, y: ey, t: 1, txt: pts}); e.modo = 'voltando'; }
      else if (e.modo === 'caca' || e.modo === 'saindo') { vidas--; estado = 'morte'; timer = 1.6; return; }
    }
  }
}
function desenharMapa(){
  ctx.fillStyle = '#060a1f'; ctx.fillRect(0, 0, cv.width, cv.height);
  for (let y = 0; y < L; y++) for (let x = 0; x < C; x++) {
    const c = grade[y][x], px = x*T, py = y*T + TOPO;
    if (c === '#') {
      ctx.fillStyle = '#121c55'; ctx.fillRect(px, py, T, T);
      ctx.strokeStyle = '#5b8cff'; ctx.lineWidth = 2; ctx.beginPath();
      if (y > 0 && grade[y-1][x] !== '#') { ctx.moveTo(px, py + 1); ctx.lineTo(px + T, py + 1); }
      if (y < L-1 && grade[y+1][x] !== '#') { ctx.moveTo(px, py + T - 1); ctx.lineTo(px + T, py + T - 1); }
      if (x > 0 && grade[y][x-1] !== '#') { ctx.moveTo(px + 1, py); ctx.lineTo(px + 1, py + T); }
      if (x < C-1 && grade[y][x+1] !== '#') { ctx.moveTo(px + T - 1, py); ctx.lineTo(px + T - 1, py + T); }
      ctx.stroke();
    } else if (c === '.') { ctx.fillStyle = '#ffd9a0'; ctx.beginPath(); ctx.arc(px + T/2, py + T/2, 3, 0, 7); ctx.fill(); }
    else if (c === 'o') { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(px + T/2, py + T/2, 6 + Math.sin(relogio*8)*1.5, 0, 7); ctx.fill(); }
    else if (c === '-') { ctx.fillStyle = '#ff8fd1'; ctx.fillRect(px, py + T/2 - 2, T, 4); }
  }
}
function desenharSlime(x, y){
  const s = 1 + Math.sin(relogio*14)*0.06, olhar = jog.dx || jog.dy ? [jog.dx, jog.dy] : [0, 0];
  ctx.save(); ctx.translate(x, y); ctx.scale(1/s, s);
  ctx.fillStyle = '#39d353'; ctx.beginPath(); ctx.arc(0, 0, 10.5, 0, 7); ctx.fill();
  ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.beginPath(); ctx.arc(-4, -5, 3.5, 0, 7); ctx.fill();
  for (const ox of [-4, 4]) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(ox, -2, 3.6, 0, 7); ctx.fill();
    ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(ox + olhar[0]*1.6, -2 + olhar[1]*1.6, 1.8, 0, 7); ctx.fill(); }
  ctx.strokeStyle = '#145a22'; ctx.lineWidth = 1.6; ctx.beginPath(); ctx.arc(0, 3, 3.5, 0.2, Math.PI - 0.2); ctx.stroke();
  ctx.restore();
}
function desenharVirus(e, x, y){
  const piscar = e.modo === 'medo' && poderT < 2 && Math.floor(relogio*8) % 2;
  const cor = e.modo === 'medo' ? (piscar ? '#fff' : '#2f6bff') : e.cor;
  ctx.save(); ctx.translate(x, y);
  if (e.modo !== 'voltando') {
    ctx.strokeStyle = cor; ctx.fillStyle = cor; ctx.lineWidth = 2;
    for (let i = 0; i < 8; i++) { const a = i*Math.PI/4 + relogio*2;
      ctx.beginPath(); ctx.moveTo(Math.cos(a)*8, Math.sin(a)*8); ctx.lineTo(Math.cos(a)*12, Math.sin(a)*12); ctx.stroke();
      ctx.beginPath(); ctx.arc(Math.cos(a)*12, Math.sin(a)*12, 2, 0, 7); ctx.fill(); }
    ctx.beginPath(); ctx.arc(0, 0, 9, 0, 7); ctx.fill();
  }
  if (e.modo === 'medo') { ctx.strokeStyle = '#fff'; ctx.lineWidth = 1.5; ctx.beginPath();
    for (let i = 0; i <= 4; i++) ctx.lineTo(-5 + i*2.5, 3 + (i % 2 ? -1.5 : 1.5)); ctx.stroke();
    ctx.fillStyle = '#fff'; ctx.fillRect(-4, -3, 2, 2); ctx.fillRect(2, -3, 2, 2); }
  else { for (const ox of [-3.5, 3.5]) { ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(ox, -1.5, 3, 0, 7); ctx.fill();
      ctx.fillStyle = '#111'; ctx.beginPath(); ctx.arc(ox + e.dx*1.3, -1.5 + e.dy*1.3, 1.6, 0, 7); ctx.fill(); }
    if (e.modo !== 'voltando') { ctx.strokeStyle = '#111'; ctx.lineWidth = 1.5; ctx.beginPath();
      ctx.moveTo(-6, -6); ctx.lineTo(-1.5, -4); ctx.moveTo(6, -6); ctx.lineTo(1.5, -4); ctx.stroke(); } }
  ctx.restore();
}
function desenhar(){
  desenharMapa();
  for (const e of inis) { const [x, y] = pos(e); desenharVirus(e, x*T + T/2, y*T + T/2 + TOPO); }
  const [jx, jy] = pos(jog);
  if (estado === 'morte') { const s = Math.max(0, timer/1.6); ctx.globalAlpha = s; desenharSlime(jx*T + T/2, jy*T + T/2 + TOPO); ctx.globalAlpha = 1; }
  else desenharSlime(jx*T + T/2, jy*T + T/2 + TOPO);
  for (const f of flutuantes) texto(f.txt, f.x*T + T/2, f.y*T + TOPO, 14, '#7df9ff');
  ctx.fillStyle = '#060a1f'; ctx.fillRect(0, 0, cv.width, TOPO);
  texto('Pontos ' + pontos, 10, TOPO/2, 16, '#fff', 'left');
  texto('Nível ' + nivel, cv.width/2, TOPO/2, 16, '#9fe6ff');
  for (let i = 0; i < vidas; i++) { ctx.fillStyle = '#39d353'; ctx.beginPath(); ctx.arc(cv.width - 16 - i*22, TOPO/2, 8, 0, 7); ctx.fill(); }
  if (estado === 'pronto') texto('PREPARE-SE!', cv.width/2, (11.5)*T + TOPO, 22, '#ffd34d');
  if (estado === 'nivel') texto('NÍVEL ' + nivel + ' COMPLETO! 🎉', cv.width/2, (11.5)*T + TOPO, 20, '#ffd34d');
  if (estado === 'inicio') painel('🟢 Come-Come', ['Coma todas as bolinhas sem ser pego', 'pelos vírus! Bolona = vírus com medo', 'Setas, arrastar o dedo ou botões', ajudaInicio()]);
  if (estado === 'pausa') painel('⏸️ Pausado', ['ESPAÇO ou toque para continuar']);
  if (estado === 'fim') painel('Fim de jogo!', ['Pontos: ' + pontos + '   ·   Nível ' + nivel, 'Recorde: ' + recorde, 'ESPAÇO ou toque para jogar de novo']);
}
"""

# ---------------------------------------------------------------- PINBALL
PINBALL_JS = r"""
const W = 400, H = 640; cv.width = W; cv.height = H;
const G = 760, R = 9;
const segs = [];
function seg(ax, ay, bx, by, o = {}){ const s = {ax, ay, bx, by, rest: o.rest ?? 0.45, kick: o.kick || 0, cor: o.cor || '#6f8cff', lw: o.lw || 5, flash: 0, gate: !!o.gate};
  segs.push(s); return s; }
function linha(pts, o){ for (let i = 0; i < pts.length - 1; i++) seg(pts[i][0], pts[i][1], pts[i+1][0], pts[i+1][1], o); }
linha([[125, 592], [10, 500], [10, 90], [28, 42], [65, 16], [110, 8], [290, 8], [335, 16], [372, 40], [395, 90], [395, 628]]);
seg(360, 628, 395, 628);                                   // fundo da canaleta
seg(360, 628, 360, 175);                                   // parede da canaleta
linha([[360, 500], [275, 592]]);
const portao = seg(360, 175, 395, 140, {gate: true, cor: '#ffd34d', lw: 3});
linha([[55, 420], [55, 492], [104, 538]], {cor: '#6f8cff'});
const estilingues = [seg(55, 420, 104, 538, {kick: 520, rest: 0.2, cor: '#ff5ea8', lw: 6}),
                     seg(305, 420, 256, 538, {kick: 520, rest: 0.2, cor: '#ff5ea8', lw: 6})];
linha([[305, 420], [305, 492], [256, 538]], {cor: '#6f8cff'});
linha([[96, 60], [96, 100]], {cor: '#6f8cff', lw: 4}); linha([[304, 60], [304, 100]], {cor: '#6f8cff', lw: 4});
const bumpers = [{x: 140, y: 190, r: 24, cor: '#ff4d6d', flash: 0}, {x: 260, y: 190, r: 24, cor: '#2ec4b6', flash: 0},
                 {x: 200, y: 280, r: 24, cor: '#ffb02e', flash: 0}];
const postes = [{x: 200, y: 120, r: 7}, {x: 30, y: 280, r: 6}, {x: 330, y: 280, r: 6}];
const luzes = [{x: 150, y: 72}, {x: 200, y: 72}, {x: 250, y: 72}];
const flippers = [{px: 125, py: 592, len: 64, lado: 1, a: 0.5, tecla: 'esq'}, {px: 275, py: 592, len: 64, lado: -1, a: 0.5, tecla: 'dir'}];
const REPOUSO = 0.5, CIMA = -0.48;
let bola, antes = 'jogando', estado = 'inicio', pontos = 0, bolas = 3, mult = 1, forca = 0, carregando = false, msg = '', msgT = 0,
    recorde = lerRecorde('rec_pinball');
function pontaFlipper(f){ return [f.px + f.lado*f.len*Math.cos(f.a), f.py + f.len*Math.sin(f.a)]; }
function novaBola(){ bola = {x: 377.5, y: 616, vx: 0, vy: 0}; bola.naMesa = false; forca = 0; carregando = false; estado = 'lancar'; }
function novoJogo(){ pontos = 0; bolas = 3; mult = 1; luzes.forEach(l => l.on = false); novaBola(); }
function aviso(t){ msg = t; msgT = 1.6; }
function aoApertar(k){
  if (k === 'acao') {
    if (estado === 'inicio' || estado === 'fim') { novoJogo(); return; }
    if (estado === 'pausa') { estado = antes; return; }
    if (estado === 'lancar') carregando = true;
  }
  if (k === 'pausa') { if (estado === 'jogando' || estado === 'lancar') { antes = estado; carregando = false; estado = 'pausa'; } else if (estado === 'pausa') estado = antes; }
}
function aoSoltar(k){
  if (k === 'acao' && estado === 'lancar' && carregando) { bola.vy = -(980 + 760*forca); carregando = false; forca = 0; estado = 'jogando'; }
}
const toques = {};
cv.addEventListener('pointerdown', e => {
  cv.focus();
  if (estado === 'inicio' || estado === 'fim' || estado === 'pausa') { aoApertar('acao'); return; }
  const r = cv.getBoundingClientRect(), x = (e.clientX - r.left)/r.width*W;
  if (estado === 'lancar' && x > 340) { toques[e.pointerId] = 'acao'; apertar('acao'); return; }
  const lado = x < W/2 ? 'esq' : 'dir'; toques[e.pointerId] = lado; apertar(lado);
});
['pointerup', 'pointercancel', 'pointerleave'].forEach(t => cv.addEventListener(t, e => {
  const l = toques[e.pointerId]; if (l) { delete toques[e.pointerId]; if (!Object.values(toques).includes(l)) soltar(l); } }));
function marcar(p){ pontos += p*mult; }
function colideSeg(ax, ay, bx, by, raio, rest, vSup){
  const dx = bx - ax, dy = by - ay; let t = ((bola.x - ax)*dx + (bola.y - ay)*dy)/(dx*dx + dy*dy);
  t = Math.max(0, Math.min(1, t));
  const px = ax + t*dx, py = ay + t*dy; let nx = bola.x - px, ny = bola.y - py; const d = Math.hypot(nx, ny);
  if (d >= raio || d === 0) return null;
  nx /= d; ny /= d; bola.x = px + nx*raio; bola.y = py + ny*raio;
  const sx = vSup ? vSup[0]*t : 0, sy = vSup ? vSup[1]*t : 0;
  const rvx = bola.vx - sx, rvy = bola.vy - sy, vn = rvx*nx + rvy*ny;
  if (vn < 0) { bola.vx = rvx - (1 + rest)*vn*nx + sx; bola.vy = rvy - (1 + rest)*vn*ny + sy; }
  return {nx, ny, vn};
}
function colideCirculo(c, rest, impulso){
  const dx = bola.x - c.x, dy = bola.y - c.y, d = Math.hypot(dx, dy), m = c.r + R;
  if (d >= m || d === 0) return false;
  const nx = dx/d, ny = dy/d; bola.x = c.x + nx*m; bola.y = c.y + ny*m;
  const vn = bola.vx*nx + bola.vy*ny;
  if (vn < 0) { bola.vx -= (1 + rest)*vn*nx; bola.vy -= (1 + rest)*vn*ny; }
  if (impulso) { const v = Math.hypot(bola.vx, bola.vy); if (v < impulso) { bola.vx += nx*(impulso - v); bola.vy += ny*(impulso - v); } }
  return true;
}
function passo(h){
  for (const f of flippers) { f.ponta0 = pontaFlipper(f); const alvo = keys[f.tecla] && estado !== 'pausa' ? CIMA : REPOUSO;
    const vel = alvo < f.a ? 24 : 12; f.a = alvo < f.a ? Math.max(alvo, f.a - vel*h) : Math.min(alvo, f.a + vel*h); }
  if (estado === 'lancar') { bola.x = 377.5; bola.y = 616; bola.vx = bola.vy = 0; return; }
  bola.vy += G*h; bola.x += bola.vx*h; bola.y += bola.vy*h;
  const v = Math.hypot(bola.vx, bola.vy); if (v > 1900) { bola.vx *= 1900/v; bola.vy *= 1900/v; }
  if (!bola.naMesa && bola.x < 350) bola.naMesa = true;
  for (const s of segs) {
    if (s.gate && !bola.naMesa) continue;
    const c = colideSeg(s.ax, s.ay, s.bx, s.by, R + s.lw/2, s.rest);
    if (c && s.kick && c.vn < -60) { bola.vx += c.nx*s.kick; bola.vy += c.ny*s.kick; s.flash = 0.15; marcar(10); }
  }
  for (const b of bumpers) if (colideCirculo(b, 0.6, 720)) { if (b.flash <= 0.05) marcar(100); b.flash = 0.18; }
  for (const p of postes) colideCirculo(p, 0.5, 0);
  for (const f of flippers) { const p = pontaFlipper(f);
    const vs = [(p[0] - f.ponta0[0])/h, (p[1] - f.ponta0[1])/h];
    colideSeg(f.px, f.py, p[0], p[1], R + 7, 0.25, vs); }
  for (const l of luzes) if (!l.on && Math.hypot(bola.x - l.x, bola.y - l.y) < 16) { l.on = true; marcar(50);
    if (luzes.every(x => x.on)) { mult = Math.min(5, mult + 1); aviso('MULTIPLICADOR x' + mult + '!'); marcar(500); setTimeout(() => luzes.forEach(x => x.on = false), 700); } }
  if (bola.y > H + 30) {
    bolas--;
    if (bolas > 0) { aviso('Bola perdida! Restam ' + bolas); novaBola(); }
    else { estado = 'fim'; recorde = salvarRecorde('rec_pinball', pontos); }
  }
}
function atualizar(dt){
  msgT -= dt; for (const b of bumpers) b.flash -= dt; for (const s of segs) s.flash -= dt;
  if (estado === 'lancar' && carregando) forca = Math.min(1, forca + dt*0.9);
  if (estado !== 'jogando' && estado !== 'lancar') return;
  const n = 10; for (let i = 0; i < n; i++) passo(dt/n);
}
function desenhar(){
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#1a0f3d'); g.addColorStop(1, '#090616');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  ctx.globalAlpha = 0.13; texto(pontos, 200, 400, 64, '#fff'); ctx.globalAlpha = 1;
  texto('x' + mult, 200, 445, 18, '#ffd34d');
  for (const l of luzes) { ctx.fillStyle = l.on ? '#ffe066' : '#3a2f66'; ctx.beginPath(); ctx.arc(l.x, l.y, 9, 0, 7); ctx.fill();
    if (l.on) { ctx.strokeStyle = 'rgba(255,224,102,.5)'; ctx.lineWidth = 4; ctx.stroke(); } }
  ctx.lineCap = 'round';
  for (const s of segs) { if (s.gate && !bola.naMesa) continue; ctx.strokeStyle = s.flash > 0 ? '#fff' : s.cor; ctx.lineWidth = s.lw;
    ctx.beginPath(); ctx.moveTo(s.ax, s.ay); ctx.lineTo(s.bx, s.by); ctx.stroke(); }
  for (const b of bumpers) { const f = b.flash > 0;
    ctx.fillStyle = f ? '#fff' : b.cor; ctx.beginPath(); ctx.arc(b.x, b.y, b.r + (f ? 3 : 0), 0, 7); ctx.fill();
    ctx.fillStyle = '#1a0f3d'; ctx.beginPath(); ctx.arc(b.x, b.y, b.r*0.55, 0, 7); ctx.fill();
    ctx.fillStyle = f ? b.cor : '#fff'; ctx.beginPath(); ctx.arc(b.x, b.y, b.r*0.3, 0, 7); ctx.fill(); }
  for (const p of postes) { ctx.fillStyle = '#9fb3ff'; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fill(); }
  for (const f of flippers) { const p = pontaFlipper(f);
    ctx.strokeStyle = '#ffd34d'; ctx.lineWidth = 15; ctx.beginPath(); ctx.moveTo(f.px, f.py); ctx.lineTo(p[0], p[1]); ctx.stroke();
    ctx.fillStyle = '#b8860b'; ctx.beginPath(); ctx.arc(f.px, f.py, 4, 0, 7); ctx.fill(); }
  ctx.fillStyle = '#2b2350'; ctx.fillRect(363, 628, 30, 10);
  if (estado === 'lancar') { ctx.fillStyle = 'rgba(255,94,168,.25)'; ctx.fillRect(366, 550, 24, 80);
    ctx.fillStyle = '#ff5ea8'; ctx.fillRect(366, 630 - forca*80, 24, forca*80); }
  const bg = ctx.createRadialGradient(bola.x - 3, bola.y - 3, 1, bola.x, bola.y, R);
  bg.addColorStop(0, '#fff'); bg.addColorStop(1, '#8a93a8');
  ctx.fillStyle = bg; ctx.beginPath(); ctx.arc(bola.x, bola.y, R, 0, 7); ctx.fill();
  texto('Bolas: ' + '⚪'.repeat(Math.max(0, bolas)), 20, 628, 13, '#cfd6ff', 'left');
  if (msgT > 0) texto(msg, 200, 340, 20, '#ffd34d');
  if (estado === 'lancar' && msgT <= 0) texto(matchMedia('(pointer: coarse)').matches ? 'Segure 🚀 e solte' : 'Segure ESPAÇO e solte', 200, 340, 17, '#ff9fd0');
  if (estado === 'inicio') painel('🪩 Pinball', ['Não deixe a bola cair entre as palhetas!', '← → (ou toque nos lados) mexem as palhetas', 'ESPAÇO / 🚀 segura e solta para lançar', ajudaInicio()]);
  if (estado === 'pausa') painel('⏸️ Pausado', ['ESPAÇO ou toque para continuar']);
  if (estado === 'fim') painel('Fim de jogo!', ['Pontos: ' + pontos, 'Recorde: ' + recorde, 'ESPAÇO ou toque para jogar de novo']);
}
novaBola(); estado = 'inicio';
"""

BOTOES_CORRIDA = '<button data-k="esq">◀ Esquerda</button><button data-k="dir">Direita ▶</button>'
BOTOES_COME = ('<button data-k="esq">◀</button><button data-k="cima">▲</button>'
               '<button data-k="baixo">▼</button><button data-k="dir">▶</button>')
BOTOES_PINBALL = '<button data-k="esq">◀ Palheta</button><button data-k="acao">🚀</button><button data-k="dir">Palheta ▶</button>'


def jogo_animado(js, largura, altura_iframe, botoes):
    pagina = pagina_canvas(js, largura, botoes)
    if hasattr(st, "iframe"):  # Streamlit novo
        st.iframe(pagina, height=altura_iframe)
    else:  # Streamlit antigo
        components.html(pagina, height=altura_iframe, scrolling=False)
    st.caption("🖱️ No computador, clique no jogo antes de usar o teclado. 📱 No celular, use os botões ou toque na tela.")


def jogo_pinball():
    jogo_animado(PINBALL_JS, 400, 730, BOTOES_PINBALL)


def jogo_comecome():
    jogo_animado(COMECOME_JS, 456, 640, BOTOES_COME)


def jogo_corrida():
    jogo_animado(CORRIDA_JS, 360, 690, BOTOES_CORRIDA)


# =====================================================================
# 👑 A VIDA É UM JOGO — Do Zero ao Império  (motor da simulação)
# =====================================================================
RAMOS = {
    "🏗️ Construção civil": dict(mercado=4500, cap0=7000, capf=14000, margem=.35, fixo=400, salario=2800, vol=.35,
        desc="Contratos grandes e lucrativos, mas o dinheiro oscila muito e a burocracia pesa."),
    "🤖 Tecnologia e IA": dict(mercado=2200, cap0=5000, capf=11000, margem=.70, fixo=300, salario=5000, vol=.25,
        desc="Margem altíssima e crescimento rápido. A equipe é cara e conhecimento vale ouro."),
    "🍔 Alimentação": dict(mercado=5000, cap0=6500, capf=9000, margem=.38, fixo=800, salario=2000, vol=.12,
        desc="Cliente todo dia e faturamento estável, porém margem apertada."),
    "🛒 Comércio": dict(mercado=6000, cap0=8000, capf=11000, margem=.30, fixo=700, salario=1900, vol=.15,
        desc="Gira bem e escala fácil, mas a guerra de preços é feroz."),
    "🧰 Prestação de serviços": dict(mercado=2500, cap0=4500, capf=6000, margem=.62, fixo=400, salario=2300, vol=.18,
        desc="Começa barato e com boa margem, mas depende muito de você e da sua reputação."),
    "🏠 Mercado imobiliário": dict(mercado=2200, cap0=7000, capf=9000, margem=.75, fixo=400, salario=3200, vol=.45,
        desc="Comissões enormes, mas meses de vacas magras. Para quem aguenta o sobe-e-desce."),
}
FASES = [  # nome, faturamento médio mensal mínimo, patrimônio mínimo
    ("🌱 Sonhador", 0, -1e12),
    ("🛠️ Autônomo", 4000, 0),
    ("🏪 Pequeno Negócio", 15000, 30000),
    ("🏢 Empresa em Crescimento", 50000, 250000),
    ("🏙️ Empresa Consolidada", 250000, 2000000),
    ("🏰 Império", 1000000, 10000000),
]
ESTRUTURAS = [("Cantinho em casa", 1), ("Salinha alugada", 4), ("Loja / escritório", 12),
              ("Andar comercial", 35), ("Sede própria", 90), ("Complexo empresarial", 250)]
CUSTO_VIDA = 1200
IND = ["rep", "rel", "saude", "felic", "conhec", "integ"]
NOME_IND = {"rep": "⭐ Reputação", "rel": "🤝 Relacionamentos", "saude": "💚 Saúde emocional",
            "felic": "😊 Felicidade", "conhec": "📚 Conhecimento", "integ": "⚖️ Integridade"}

NOMES_M = ["Roberto", "Carlos", "Marcos", "Eduardo", "Fábio", "Rafael", "Thiago", "Leandro", "Gustavo",
           "Paulo", "Henrique", "Sérgio", "Diego", "Vinícius", "Rodrigo", "André"]
NOMES_F = ["Juliana", "Patrícia", "Camila", "Fernanda", "Renata", "Larissa", "Beatriz", "Vanessa",
           "Aline", "Marina", "Cláudia", "Débora", "Bianca", "Letícia", "Priscila", "Tatiane"]
PAPEIS = {
    "socio": dict(titulo="🤝 Sócio(a) em potencial", bom=.4,
                  b="empresário(a) honesto(a) e experiente, cauteloso(a) com promessas, faz questão de contrato bem feito",
                  r="oportunista que quer o capital do jogador e fugir das responsabilidades; exagera contatos, apressa decisões, evita falar de contrato"),
    "amigo": dict(titulo="🫂 Amigo(a) de longa data", bom=.65,
                  b="amigo(a) leal de verdade, sincero(a), às vezes diz verdades duras porque se importa",
                  r="falso(a) amigo(a): bajula quando há dinheiro, pede favores, some nas horas difíceis e fala mal dos outros"),
    "novo_amigo": dict(titulo="🥂 Amigo(a) novo(a) do sucesso", bom=.3,
                       b="pessoa bem-sucedida que admira o jogador de verdade e gosta de ajudar sem interesse",
                       r="aproveitador(a) que surgiu quando o jogador prosperou, vive de aparências e de 'negócios garantidos'"),
    "consultor": dict(titulo="📊 Consultor(a)", bom=.65,
                      b="consultor(a) competente, faz perguntas difíceis, mostra números, cobra caro mas entrega",
                      r="consultor(a) de palco: frases de efeito, slides bonitos, nenhum plano concreto"),
    "advogado": dict(titulo="⚖️ Advogado(a)", bom=.85,
                     b="advogado(a) cuidadoso(a) e ético(a), aponta riscos em contratos e recomenda prudência",
                     r="advogado(a) que só pensa em honorários e incentiva brigas judiciais desnecessárias"),
    "investidor": dict(titulo="💼 Investidor(a)", bom=.6,
                       b="investidor(a) sério(a), quer crescer junto, respeita a cultura da empresa",
                       r="investidor(a) predador(a): quer controle total, cortar custos a qualquer preço e vender a empresa"),
    "concorrente": dict(titulo="🦈 Concorrente", bom=.15,
                        b="concorrente duro(a) mas leal, compete com qualidade e respeita regras",
                        r="concorrente desleal: espalha boatos, rouba funcionários e clientes, blefa o tempo todo"),
    "amor": dict(titulo="❤️ Interesse amoroso", bom=.5,
                 b="pessoa genuína, gosta do jogador independentemente do dinheiro, pergunta sobre sentimentos, sonhos e família",
                 r="pessoa interesseira: muito carinhosa, mas sempre puxa assunto sobre patrimônio, presentes, viagens caras e conta conjunta"),
    "mentor": dict(titulo="🧓 Mentor(a)", bom=.85,
                   b="empresário(a) veterano(a) generoso(a) que ensina com histórias reais de erros e acertos",
                   r="empresário(a) vaidoso(a) que dá conselhos para se promover e cobra favores depois"),
}
PISTAS = {
    True: ["Ex-parceiros falam muito bem de {n}.", "{n} tem nome limpo, sem processos na Justiça.",
           "Gente próxima diz que {n} sempre cumpre o que promete.", "{n} ajudou um conhecido seu de graça no ano passado."],
    False: ["Há processos por calote no nome de {n}.", "Um antigo colega diz que {n} 'some quando a coisa aperta'.",
            "{n} já abriu e fechou quatro empresas em cinco anos.", "Uma pessoa confidenciou que {n} vive pedindo dinheiro emprestado."],
}

CONQUISTAS = {
    "primeiro_lucro": ("💵 Primeiro Lucro", "Feche um mês no azul."),
    "primeiro_func": ("👥 Agora Somos Dois", "Contrate seu primeiro funcionário."),
    "colchao": ("🛟 Colchão de Segurança", "Tenha R$ 20 mil em caixa."),
    "fase2": ("🏪 Pequeno Negócio", "Chegue à fase Pequeno Negócio."),
    "fase3": ("🏢 Em Crescimento", "Chegue à fase Empresa em Crescimento."),
    "fase4": ("🏙️ Consolidado", "Chegue à fase Empresa Consolidada."),
    "fase5": ("🏰 IMPÉRIO", "Chegue à fase Império."),
    "milhao": ("💎 Primeiro Milhão", "Tenha patrimônio de R$ 1 milhão."),
    "sequencia": ("🔥 Máquina de Lucro", "Lucre 6 meses seguidos."),
    "sem_divida": ("🕊️ Livre de Dívidas", "Quite totalmente uma dívida."),
    "detetive": ("🕵️ Detetive", "Desmascare alguém antes de sair no prejuízo."),
    "licao": ("🩹 Lição Cara", "Caia num golpe (acontece com os melhores)."),
    "maos_limpas": ("🧼 Mãos Limpas", "Chegue ao mês 24 com integridade 90 ou mais."),
    "familia": ("🏡 Coração em Primeiro Lugar", "Tenha relacionamentos 90 ou mais."),
    "amor": ("💍 Amor Verdadeiro", "Case com uma pessoa genuína."),
    "empregos": ("🏭 Gerador de Empregos", "Tenha 10 funcionários."),
    "sobrevivente": ("🎂 5 Anos de Estrada", "Sobreviva 60 meses."),
    "familia_formada": ("👶 Família Formada", "Tenha um filho."),
    "amor_que_dura": ("💞 Amor que Dura", "Chegue ao mês 60 casado(a) e com atenção ao relacionamento acima de 70."),
    "superacao": ("🌅 Superação", "Recupere a saúde emocional (70+) depois de uma traição."),
    "vida_plena": ("🌈 Vida Plena", "Tenha as 5 dimensões da vida em 70 ou mais."),
}


def brl(v):
    return ("-R$ " if v < 0 else "R$ ") + f"{abs(v):,.0f}".replace(",", ".")


def ele(p):
    return "ele" if p["sexo"] == "M" else "ela"


def oa(p):
    return "o" if p["sexo"] == "M" else "a"


def mudar(e, **kw):
    for k, v in kw.items():
        if k in ("caixa", "divida"):
            e[k] += v
        elif k == "mercado":  # multiplicador
            e["mercado"] = max(300, e["mercado"] * v)
        else:
            e[k] = max(0, min(100, e[k] + v))


def log(e, texto, pid=None):
    e["diario"].append((e["mes"], texto, pid))


def agendar(e, meses, fn):
    e["pend"].append({"mes": e["mes"] + meses, "fn": fn})


def forcar(e, meses, ev_id):
    e["forcados"].append({"mes": e["mes"] + meses, "ev": ev_id})


def conquistar(e, cid):
    if cid not in e["conquistas"]:
        e["conquistas"].add(cid)
        e["novas_conq"].append(cid)


def media(lista, n=3):
    ult = lista[-n:]
    return sum(ult) / len(ult) if ult else 0


def receita_media(e):
    return media(e["hist_receita"]) if e["hist_receita"] else e["r"]["mercado"]


def valor_empresa(e):
    """Lucro líquido médio × um múltiplo que cresce com o tamanho da empresa."""
    liquido = media(e["hist_lucro_op"]) - CUSTO_VIDA
    return max(0, liquido) * (6 + min(30, 2 * e["func"] + 4 * e["estrutura"]))


def patrimonio(e):
    return e["caixa"] - e["divida"] + valor_empresa(e) * e["part"]


def limite_credito(e):
    return max(0, 5000 + receita_media(e) * 3 + e["rep"] * 100 - e["divida"])


def sat(e):
    """Quanto maior o negócio, mais difícil crescer (saturação de mercado)."""
    return 1 / (1 + e["mercado"] / 40000)


def capacidade(e):
    cap = e["r"]["cap0"] + e["func"] * e["r"]["capf"]
    return cap * (0.7 if e["saude"] < 20 else 1)


def margem(e):
    return min(0.92, e["r"]["margem"] + e["conhec"] / 1000 + e["bonus_margem"])


def custo_fixo(e):
    return e["r"]["fixo"] * (1.8 ** e["estrutura"])


def folha(e):
    return e["func"] * e["r"]["salario"] * (1 + e["extra_salario"])


def fase_atual(e):
    rm, pat, f = receita_media(e), patrimonio(e), 0
    for i, (_, fat, pmin) in enumerate(FASES):
        if rm >= fat and pat >= pmin:
            f = i
    return f


def dimensoes(e):
    pat = patrimonio(e)
    pros = 0 if pat <= 1000 else min(100, 20 * math.log10(pat / 1000))
    return {
        "💰 Prosperidade": round(pros),
        "🏢 Empresa": round(min(100, e["fase_max"] * 16 + e["rep"] * 0.2)),
        "🌿 Qualidade de vida": round((e["saude"] + e["felic"]) / 2),
        "🤝 Relacionamentos": round(e["rel"]),
        "⚖️ Integridade": round(e["integ"]),
    }


def pontuacao(e):
    return int(sum(dimensoes(e).values()) * 2)


def titulo_vida(pts):
    for lim, t in [(200, "Sobrevivente em Apuros"), (400, "Batalhador(a)"), (550, "Empreendedor(a) de Verdade"),
                   (700, "Referência no Mercado"), (850, "Lenda dos Negócios")]:
        if pts < lim:
            return t
    return "👑 Mestre da Vida"


def nova_pessoa(e, papel, forcar_bom=None):
    usados = {p["nome"] for p in e["pessoas"].values()}
    sexo = random.choice("MF")
    nomes = [n for n in (NOMES_M if sexo == "M" else NOMES_F) if n not in usados] or ["Alex"]
    pid = f"p{len(e['pessoas'])}"
    bom = forcar_bom if forcar_bom is not None else random.random() < PAPEIS[papel]["bom"]
    p = dict(id=pid, nome=random.choice(nomes), sexo=sexo, idade=random.randint(26, 62), papel=papel,
             bom=bom, pistas=[], ativo=True, revelado=False, conheceu=e["mes"])
    e["pessoas"][pid] = p
    e["chats"][pid] = []
    log(e, f"Você conheceu {p['nome']} ({PAPEIS[papel]['titulo']}).", pid)
    return p


def pessoa(e, papel, criar=True):
    for p in e["pessoas"].values():
        if p["papel"] == papel and p["ativo"]:
            return p
    return nova_pessoa(e, papel) if criar else None


def investigar(e, p):
    verdade = p["bom"] if random.random() < 0.8 else not p["bom"]
    pista = random.choice(PISTAS[verdade]).format(n=p["nome"])
    if pista not in p["pistas"]:
        p["pistas"].append(pista)
    return pista


def revelar(e, p):
    p["revelado"] = True
    if not p["bom"]:
        log(e, f"🚩 Você descobriu quem {p['nome']} realmente é.", p["id"])


def novo_jogo_vida(jogador, empresa, ramo, legado=0):
    r = dict(RAMOS[ramo])
    e = dict(jogador=jogador, empresa=empresa, ramo=ramo, r=r, mes=1, caixa=3000.0, divida=0.0, taxa=0.0,
             mercado=float(r["mercado"]), func=0, estrutura=0, part=1.0, bonus_margem=0.0, extra_salario=0.0,
             vida_mult=1.0, rep=40, rel=60, saude=80, felic=65, conhec=15 + legado, integ=70,
             hist_receita=[], hist_lucro_op=[], hist_resultado=[], pessoas={}, chats={}, diario=[], pend=[], forcados=[],
             conquistas=set(), novas_conq=[], usados=[], ja=set(), flags=set(), fase_max=0, seq_lucro=0,
             etapa="acao", ev=None, resultados=[], noticias=[], relatorio=None, fim=None, teve_divida=False,
             parceiro=None, socio=None, avaliacao5=False, atencao=60, regime=None, filhos=0,
             namoro_desde=None)
    nova_pessoa(e, "amigo")
    log(e, f"Você abriu \"{empresa}\" no ramo {ramo} com {brl(3000)} no bolso e um computador velho. Começa a jornada!")
    e["prox"] = escolher_evento(e)
    return e


# ---------------------------------------------------------------- AÇÕES DO MÊS
def acoes_disponiveis(e):
    rm = receita_media(e)
    mkt = max(500, round(rm * 0.3, -2))
    estudo = 400 + 300 * e["fase_max"]
    inov = round(1000 + rm * 0.4, -2)
    amp = round(2500 * 2.6 ** e["estrutura"], -2)
    lista = [
        ("💼 Vender e prospectar", "Bater de porta em porta atrás de clientes. Mercado +12%, mas cansa.", 0, "vender"),
        (f"📣 Marketing ({brl(mkt)})", "Anúncios e redes sociais. Traz bastante cliente novo.", mkt, "marketing"),
        (f"📚 Estudar e se capacitar ({brl(estudo)})", "Cursos e livros. Conhecimento melhora margem e decisões.", estudo, "estudar"),
        ("🍻 Networking em eventos (R$ 300)", "Conhecer gente nova. Rende contatos e oportunidades.", 300, "network"),
        ("🧘 Cuidar de você e da família", "Recarregar as energias. O negócio cresce um pouco menos.", 0, "descansar"),
        (f"💡 Inovar o produto ({brl(inov)})", "Melhorar o que você vende. Margem e clientes sobem.", inov, "inovar"),
    ]
    if e["estrutura"] < len(ESTRUTURAS) - 1:
        prox = ESTRUTURAS[e["estrutura"] + 1]
        lista.append((f"🏗️ Mudar para: {prox[0]} ({brl(amp)})",
                      f"Comporta até {prox[1]} funcionários. Aumenta reputação e custo fixo.", amp, "ampliar"))
    return lista


def fazer_acao(e, chave, custo):
    e["caixa"] -= custo
    txt = ""
    if chave == "vender":
        e["mercado"] += e["mercado"] * 0.12 * sat(e) + 600
        mudar(e, saude=-5, rep=+1)
        txt = "Você rodou a cidade oferecendo seu trabalho e fechou novos clientes."
    elif chave == "marketing":
        e["mercado"] += custo * 1.6 * sat(e)
        mudar(e, rep=+2)
        txt = "A campanha viralizou um pouco, e o telefone não parou de tocar."
    elif chave == "estudar":
        mudar(e, conhec=+8, saude=-2, felic=+2)
        txt = "Você estudou finanças, vendas e gestão. Está enxergando coisas que antes passavam batido."
    elif chave == "network":
        e["mercado"] *= 1.03
        mudar(e, rel=+6, rep=+2, saude=-2)
        txt = "Você trocou muitos cartões e fez contatos interessantes."
        if random.random() < 0.55:
            forcar(e, 1, random.choice(["consultor", "mentor", "amor_conhecer", "investidor"]))
            txt += " Alguém em especial ficou com seu contato…"
    elif chave == "descansar":
        e["mercado"] *= 0.96
        mudar(e, saude=+16, felic=+10, rel=+6)
        e["atencao"] = min(100, e.get("atencao", 60) + 35)
        txt = "Você desligou o celular, dormiu bem e jantou com quem ama. Voltou outra pessoa."
    elif chave == "inovar":
        e["bonus_margem"] = min(0.15, e["bonus_margem"] + 0.02)
        e["mercado"] *= 1.06
        mudar(e, conhec=+3, rep=+2)
        txt = "O produto ficou melhor e mais lucrativo. Os clientes perceberam."
    elif chave == "ampliar":
        e["estrutura"] += 1
        mudar(e, rep=+5, felic=+5)
        txt = f"Você mudou para: {ESTRUTURAS[e['estrutura']][0]}! Mais espaço, mais custo, mais respeito."
    log(e, txt)
    return txt


def contratar(e, n):
    custo = n * e["r"]["salario"] * 0.5
    e["caixa"] -= custo
    e["func"] += n
    conquistar(e, "primeiro_func")
    if e["func"] >= 10:
        conquistar(e, "empregos")
    log(e, f"Você contratou {n} pessoa(s). Custo de recrutamento: {brl(custo)}.")


def demitir(e, n):
    custo = n * e["r"]["salario"] * 1.2
    e["caixa"] -= custo
    e["func"] -= n
    mudar(e, rel=-2 * n, felic=-2)
    log(e, f"Você demitiu {n} pessoa(s) e pagou {brl(custo)} de rescisão.")


def pegar_emprestimo(e, valor, taxa=0.035):
    e["taxa"] = (e["divida"] * e["taxa"] + valor * taxa) / (e["divida"] + valor)
    e["divida"] += valor
    e["caixa"] += valor
    e["teve_divida"] = True
    log(e, f"🏦 Empréstimo de {brl(valor)} a {taxa * 100:.1f}% ao mês.")


def amortizar(e, valor):
    valor = min(valor, e["divida"], max(0, e["caixa"]))
    e["caixa"] -= valor
    e["divida"] -= valor
    if e["divida"] < 1:
        e["divida"], e["taxa"] = 0, 0
        if e["teve_divida"]:
            conquistar(e, "sem_divida")
    log(e, f"🏦 Você pagou {brl(valor)} da dívida.")


# ---------------------------------------------------------------- FECHAMENTO DO MÊS
def fechar_mes(e):
    antes = {k: e[k] for k in IND + ["caixa", "divida", "func"]}
    antes["patrimonio"] = patrimonio(e)
    fase_antes = e["fase_max"]
    cap = capacidade(e)
    vendido = min(e["mercado"], cap) * random.uniform(1 - e["r"]["vol"] / 2, 1 + e["r"]["vol"] / 2)
    receita = max(0.0, vendido)
    lucro_bruto = receita * margem(e)
    fixo, salarios = custo_fixo(e), folha(e)
    juros = e["divida"] * e["taxa"]
    vida = (CUSTO_VIDA * e["vida_mult"] * (1 + 0.15 * e["fase_max"]) * (1.25 if "casado" in e["flags"] else 1)
            * (1 + 0.35 * e.get("filhos", 0)))
    lucro_op = lucro_bruto - fixo - salarios
    resultado = lucro_op - juros - vida
    e["caixa"] += resultado
    e["hist_receita"].append(receita)
    e["hist_lucro_op"].append(lucro_op)
    e["hist_resultado"].append(resultado)
    noticias = e["noticias"] = []

    # mercado e desgaste
    if e["mercado"] > cap * 1.3:
        mudar(e, rep=-2, felic=-1)
        noticias.append("😤 Tem mais cliente do que você consegue atender. Gente reclamando da demora: contrate!")
    saturacao = sat(e)
    e["mercado"] = max(300.0, e["mercado"] * (1 + (0.006 + (e["rep"] - 50) / 1200) * saturacao))
    mudar(e, saude=-(3 + (1 if e["func"] == 0 else 0)) + (2 if e["func"] >= 5 else 0))
    if resultado > 0:
        e["seq_lucro"] += 1
        mudar(e, felic=+1)
        conquistar(e, "primeiro_lucro")
        if e["seq_lucro"] >= 6:
            conquistar(e, "sequencia")
    else:
        e["seq_lucro"] = 0
        mudar(e, felic=-2)
    if e["divida"] > receita_media(e) * 6 and e["divida"] > 10000:
        mudar(e, saude=-3, felic=-2)
        noticias.append("😰 A dívida está tirando seu sono.")

    # consequências que chegaram
    vencidos = [p for p in e["pend"] if p["mes"] <= e["mes"]]
    e["pend"] = [p for p in e["pend"] if p["mes"] > e["mes"]]
    for p in vencidos:
        msg = p["fn"](e)
        if msg:
            noticias.append(msg)
            log(e, msg)

    if e["saude"] <= 0:
        e["caixa"] -= 3000
        e["mercado"] *= 0.7
        e["saude"] = 35
        msg = "🚑 Você teve um esgotamento (burnout) e ficou internado(a). Conta do hospital: R$ 3.000, e clientes sumiram."
        noticias.append(msg)
        log(e, msg)

    # caixa negativo → cheque especial ou falência
    if e["caixa"] < 0:
        falta = -e["caixa"] + 500
        if limite_credito(e) >= falta:
            pegar_emprestimo(e, falta, taxa=0.08)
            mudar(e, saude=-3)
            noticias.append(f"⚠️ O caixa ficou negativo e o banco cobriu com cheque especial: {brl(falta)} a 8% ao mês!")
        else:
            e["fim"] = "falencia"

    # fase e conquistas
    f = fase_atual(e)
    if f > e["fase_max"]:
        e["fase_max"] = f
        for i in range(2, f + 1):
            conquistar(e, f"fase{i}")
        log(e, f"🚀 Sua empresa chegou à fase {FASES[f][0]}!")
    if e["caixa"] >= 20000:
        conquistar(e, "colchao")
    if patrimonio(e) >= 1_000_000:
        conquistar(e, "milhao")
    if e["mes"] >= 24 and e["integ"] >= 90:
        conquistar(e, "maos_limpas")
    if e["rel"] >= 90:
        conquistar(e, "familia")
    if e["mes"] >= 60:
        conquistar(e, "sobrevivente")
    vida_afetiva_mes(e, noticias)
    if "traido" in e["flags"] and e["saude"] >= 70:
        conquistar(e, "superacao")
    if min(dimensoes(e).values()) >= 70:
        conquistar(e, "vida_plena")

    e["relatorio"] = dict(mes=e["mes"], receita=receita, lucro_bruto=lucro_bruto, fixo=fixo, salarios=salarios,
                          juros=juros, vida=vida, resultado=resultado, antes=antes, fase_antes=fase_antes,
                          cap=cap, demanda=e["mercado"])
    e["mes"] += 1
    if not e["fim"]:
        e["prox"] = escolher_evento(e)
    e["etapa"] = "fim" if e["fim"] else "relatorio"


# ---------------------------------------------------------------- EVENTOS
EVENTOS = {}


def evento(eid, titulo, teaser, cond=lambda e: True, peso=1.0, unico=False, cooldown=6):
    def reg(fn):
        EVENTOS[eid] = dict(id=eid, titulo=titulo, teaser=teaser, cond=cond, peso=peso, unico=unico,
                            cooldown=cooldown, montar=fn)
        return fn
    return reg


def escolher_evento(e):
    due = [f for f in e["forcados"] if f["mes"] <= e["mes"] and EVENTOS[f["ev"]]["cond"](e)
           and not (EVENTOS[f["ev"]]["unico"] and f["ev"] in e["ja"])]
    if e["saude"] < 30 and "saude_alerta" not in e["usados"][-3:]:
        return "saude_alerta"
    if due:
        e["forcados"].remove(due[0])
        return due[0]["ev"]
    e["forcados"] = [f for f in e["forcados"] if f["mes"] >= e["mes"] - 6]
    cands = []
    for ev in EVENTOS.values():
        if ev["peso"] <= 0 or not ev["cond"](e):
            continue
        if ev["unico"] and ev["id"] in e["ja"]:
            continue
        if ev["id"] in e["usados"][-ev["cooldown"]:]:
            continue
        cands.append(ev)
    if not cands:
        return "mes_tranquilo"
    return random.choices(cands, weights=[c["peso"] for c in cands])[0]["id"]


def montar_evento(e, eid):
    e["usados"].append(eid)
    e["ja"].add(eid)
    texto, opcoes = EVENTOS[eid]["montar"](e)
    return dict(id=eid, titulo=EVENTOS[eid]["titulo"], texto=texto, opcoes=opcoes)


# --- 1. Burocracia
@evento("burocracia", "📄 A papelada chegou", "Um envelope pardo da prefeitura está na sua mesa…",
        cond=lambda e: e["fase_max"] <= 2, peso=1.2, unico=False, cooldown=14)
def _(e):
    custo = 600 + 400 * e["fase_max"]

    def desp(e):
        mudar(e, caixa=-custo, saude=+2)
        return f"O despachante resolveu tudo em uma semana. Custou {brl(custo)}, mas você dormiu tranquilo."

    def sozinho(e):
        mudar(e, saude=-8, conhec=+5)
        if random.random() < 0.4:
            multa = custo * 2

            def cobra(e):
                mudar(e, caixa=-multa, rep=-3)
                return f"📄 Um erro na papelada que você fez sozinho virou multa de {brl(multa)}."
            agendar(e, 2, cobra)
        return "Você perdeu noites em filas e sites do governo, mas aprendeu como a burocracia funciona."
    return ("Alvará, licença, inscrição municipal… uma pilha de documentos com prazo curto. Errar pode custar caro.",
            [(f"🧾 Contratar despachante (−{brl(custo)})", desp), ("💪 Resolver sozinho", sozinho)])


# --- 2. Falta de dinheiro
@evento("sem_caixa", "💸 O dinheiro está acabando", "Você abriu o app do banco e prendeu a respiração…",
        cond=lambda e: e["caixa"] < CUSTO_VIDA * 2, peso=3, cooldown=4)
def _(e):
    valor = round(max(8000, receita_media(e) * 2), -3)

    def banco(e):
        pegar_emprestimo(e, valor, 0.04)
        return f"O gerente liberou {brl(valor)} a 4% ao mês. Fôlego agora, conta depois."

    def socio(e):
        e["seguinte"] = "socio_proposta"
        return "Você espalhou que procura um sócio. No dia seguinte, alguém ligou…"

    def cinto(e):
        e["vida_mult"] = 0.6
        mudar(e, felic=-10, rel=-5, integ=+2)

        def volta(e):
            e["vida_mult"] = 1.0
            return "🍽️ O aperto de cinto acabou. Dá para voltar a viver um pouco."
        agendar(e, 3, volta)
        return "Sem restaurante, sem lazer, arroz e ovo por 3 meses. Dói, mas sem juros."
    return (f"O caixa está em {brl(e['caixa'])}. As contas do mês que vem não fecham. O que fazer?",
            [(f"🏦 Pegar empréstimo de {brl(valor)} (4% a.m.)", banco), ("🤝 Procurar um sócio", socio),
             ("✂️ Cortar gastos pessoais por 3 meses", cinto)])


# --- 3. Concorrência
@evento("concorrencia", "🏪 Abriu um concorrente na esquina", "Tem uma faixa de 'INAUGURAÇÃO' do outro lado da rua…",
        cond=lambda e: e["mes"] > 3, peso=1, cooldown=12)
def _(e):
    custo = round(1500 + receita_media(e) * 0.3, -2)

    def preco(e):
        e["mercado"] *= 1.12
        e["bonus_margem"] -= 0.05

        def volta(e):
            e["bonus_margem"] += 0.05
            return "🏷️ A guerra de preços esfriou e você voltou a cobrar o preço normal."
        agendar(e, 6, volta)
        return "Você baixou o preço. Segurou os clientes, mas está trabalhando mais para ganhar menos."

    def inovar(e):
        e["caixa"] -= custo
        if random.random() < 0.45 + e["conhec"] / 200:
            e["mercado"] *= 1.3
            e["bonus_margem"] = min(0.15, e["bonus_margem"] + 0.03)
            mudar(e, rep=+5)
            return "Sua novidade virou assunto na cidade! O concorrente é que ficou preocupado."
        mudar(e, conhec=+5)
        return "A inovação não pegou. Você gastou, mas aprendeu o que o cliente NÃO quer."

    def ignorar(e):
        e["mercado"] *= 0.88
        return "Você fingiu que não viu. Alguns clientes foram experimentar o concorrente."
    return ("Um concorrente bem financiado abriu perto de você com preços agressivos.",
            [("🏷️ Baixar o preço", preco), (f"💡 Inovar e se diferenciar (−{brl(custo)})", inovar),
             ("🙈 Ignorar", ignorar)])


# --- 4. Cliente inadimplente
@evento("inadimplente", "🧾 O cliente não pagou", "Um cliente grande parou de responder suas mensagens…",
        cond=lambda e: receita_media(e) > 2500, peso=1, cooldown=10)
def _(e):
    v = round(receita_media(e) * 0.6, -2)

    def negociar(e):
        e["caixa"] += v * 0.6
        return f"Você aceitou receber {brl(v * 0.6)} à vista. Não é tudo, mas está no bolso."

    def justica(e):
        e["caixa"] -= 600
        adv = pessoa(e, "advogado")
        chance = 0.55 + (0.3 if adv["bom"] else 0)

        def sentenca(e):
            if random.random() < chance:
                e["caixa"] += v * 1.1
                return f"⚖️ Você ganhou o processo contra o cliente caloteiro! Entraram {brl(v * 1.1)} com correção."
            return "⚖️ Você perdeu o processo do cliente caloteiro. O dinheiro não volta."
        agendar(e, 4, sentenca)
        return f"{adv['nome']}, advogad{oa(adv)}, entrou com a ação. Resultado em uns 4 meses."

    def esquecer(e):
        mudar(e, felic=-4, rel=+2)
        return "Você deixou para lá. Raiva engolida, mas sem perder mais tempo."
    return (f"Um cliente deve {brl(v)} e sumiu.",
            [(f"🤝 Negociar e receber 60% agora", negociar), ("⚖️ Entrar na Justiça (−R$ 600)", justica),
             ("🕊️ Deixar para lá", esquecer)])


# --- 5. Funcionário desonesto
@evento("func_desonesto", "🕳️ Sumiu dinheiro do caixa", "Os números do caixa não estão batendo…",
        cond=lambda e: e["func"] >= 1, peso=1, cooldown=12)
def _(e):
    culpado = random.random() < 0.55
    perda = round(max(800, receita_media(e) * 0.4), -2)

    def investigar_f(e):
        e["caixa"] -= 500
        if culpado:
            e["func"] -= 1
            mudar(e, rep=+2, integ=+3)
            conquistar(e, "detetive")
            return "As câmeras mostraram tudo. Você demitiu o funcionário por justa causa. A equipe respeitou."
        mudar(e, rel=+4)
        e["mercado"] *= 1.04
        return "Era um erro do sistema de pagamento! O funcionário ficou grato por você não ter acusado sem provas."

    def confiar(e):
        if culpado:
            def rombo(e):
                e["caixa"] -= perda * 2
                mudar(e, felic=-6)
                conquistar(e, "licao")
                return f"🕳️ O desvio continuou e virou um rombo de {brl(perda * 2)}. Confiança sem verificação custa caro."
            agendar(e, 2, rombo)
            return "Você decidiu confiar na equipe e não fez nada."
        mudar(e, rel=+3)
        return "Você confiou, e estava certo: era um erro de troco. A equipe gosta de trabalhar com você."

    def demitir_f(e):
        e["func"] -= 1
        mudar(e, integ=-8, rep=-4)
        if not culpado:
            def processo(e):
                e["caixa"] -= e["r"]["salario"] * 3
                mudar(e, rep=-4)
                return f"⚖️ O funcionário demitido sem provas era inocente e te processou: {brl(e['r']['salario'] * 3)}."
            agendar(e, 3, processo)
        return "Você demitiu o principal suspeito sem provas. O clima na equipe ficou pesado."
    return (f"Faltam {brl(perda)} no caixa e há um funcionário suspeito.",
            [("🔎 Investigar com câmeras e auditoria (−R$ 500)", investigar_f), ("🙏 Confiar na equipe", confiar),
             ("🚪 Demitir o suspeito na hora", demitir_f)])


# --- 6. Impostos
@evento("impostos", "🏛️ Impostos atrasados", "Uma carta da Receita Federal com letras vermelhas…",
        cond=lambda e: receita_media(e) > 3000, peso=1, cooldown=12)
def _(e):
    v = round(receita_media(e) * 0.4, -2)

    def parcelar(e):
        e["divida"] += v
        e["taxa"] = (e["taxa"] * (e["divida"] - v) + v * 0.015) / e["divida"]
        e["teve_divida"] = True
        return f"Você parcelou {brl(v)} com juros baixos (1,5% a.m.). Dívida organizada."

    def pagar(e):
        e["caixa"] -= v
        mudar(e, rep=+2, integ=+3)
        return f"Pago à vista: {brl(v)}. Nome limpo e consciência tranquila."

    def arriscar(e):
        mudar(e, integ=-6)
        e["flags"].add("sonegou")
        if random.random() < 0.45:
            def multa(e):
                e["caixa"] -= v * 2
                mudar(e, rep=-8)
                return f"🏛️ A Receita voltou com multa e juros: {brl(v * 2)}. E a notícia se espalhou."
            agendar(e, 3, multa)
        return "Você deixou para depois e torceu para ninguém lembrar…"
    return (f"Você tem {brl(v)} de impostos em atraso.",
            [("📑 Parcelar", parcelar), (f"💳 Pagar à vista (−{brl(v)})", pagar), ("🎲 Deixar quieto e arriscar", arriscar)])


# --- 7. Grande oportunidade
@evento("oportunidade", "🎯 Uma oportunidade de ouro?", "Um fornecedor ligou com uma proposta 'imperdível'…",
        cond=lambda e: e["mes"] > 2, peso=1.2, cooldown=6)
def _(e):
    v = round(max(2000, receita_media(e) * 1.5), -2)
    chance = min(0.85, 0.45 + e["conhec"] / 250)

    def investir(e):
        e["caixa"] -= v
        sucesso = random.random() < chance

        def retorno(e):
            if sucesso:
                e["caixa"] += v * 2.6
                mudar(e, rep=+3, felic=+5)
                return f"🎯 A aposta deu certo! Retorno de {brl(v * 2.6)}."
            e["caixa"] += v * 0.3
            mudar(e, felic=-5)
            return f"🎯 A 'oportunidade de ouro' micou. Você recuperou só {brl(v * 0.3)}."
        agendar(e, 3, retorno)
        return f"Você investiu {brl(v)}. O resultado sai em 3 meses. (Pelo seu conhecimento, a chance parece de {chance:.0%}.)"

    def preservar(e):
        mudar(e, saude=+2)
        return "Você preservou o caixa. Talvez tenha perdido algo, talvez tenha se livrado de uma furada."
    return (f"Um lote de mercadoria/serviço com potencial de quase triplicar em 3 meses. Precisa de {brl(v)} agora.",
            [(f"💰 Investir {brl(v)}", investir), ("🛡️ Preservar o caixa", preservar)])


# --- 8. Sócio
@evento("socio_proposta", "🤝 Proposta de sociedade", "Alguém de terno pediu uma reunião 'urgente e confidencial'…",
        cond=lambda e: e["socio"] is None, peso=0.8, cooldown=18)
def _(e):
    p = pessoa(e, "socio")
    v = round(max(3000, e["caixa"] * 0.6), -2)
    e["socio_valor"] = v
    fala = random.choice([
        "Tenho contatos importantes e consigo dobrar seu faturamento em seis meses. Só preciso que você entre com o capital.",
        "Seu negócio tem potencial, mas falta gente grande. Eu trago os clientes, você entra com o dinheiro.",
        "Eu já fiz isso antes. Juntos a gente cresce rápido, mas tem que decidir logo, tenho outros interessados."])

    def inv(e):
        e["caixa"] -= 300
        pista = investigar(e, p)
        e["seguinte"] = "socio_decisao"
        return f"🔎 Você pesquisou sobre {p['nome']}: \"{pista}\""

    def adv(e):
        e["caixa"] -= 1200
        a = pessoa(e, "advogado")
        e["seguinte"] = "socio_decisao"
        if not p["bom"]:
            p["pistas"].append(f"O contrato de {p['nome']} deixava TODAS as dívidas no seu nome.")
            return f"⚖️ {a['nome']} leu o contrato e ficou pálid{oa(a)}: as dívidas ficariam só com você!"
        p["pistas"].append(f"O contrato proposto por {p['nome']} é justo e equilibrado.")
        return f"⚖️ {a['nome']} analisou: contrato equilibrado, sem pegadinhas."
    return (f"**{p['nome']}, {p['idade']} anos**, quer ser seu sócio. *\"{fala}\"* Quer {brl(v)} seus.",
            [("🔎 Investigar o histórico (−R$ 300)", inv), ("⚖️ Advogado analisa a proposta (−R$ 1.200)", adv)]
            + _opcoes_socio(e, p, v))


def _opcoes_socio(e, p, v):
    def aceitar(e):
        e["caixa"] -= v
        e["socio"] = p["id"]
        e["part"] *= 0.75
        log(e, f"Você virou sócio(a) de {p['nome']} com {brl(v)}.", p["id"])
        if p["bom"]:
            def contatos(e):
                e["mercado"] *= 1.4
                mudar(e, rep=+5, rel=+3)
                revelar(e, p)
                return f"🤝 Os contatos de {p['nome']} trouxeram clientes grandes! Mercado +40%."
            agendar(e, 2, contatos)
            agendar(e, 6, contatos)
        else:
            p["bomba"] = e["mes"] + 5
            forcar(e, 2, "segredo_socio")

            def fuga(e):
                if e["socio"] != p["id"]:
                    return None
                perda = v * 0.5
                e["caixa"] -= perda
                e["divida"] += v
                e["taxa"] = max(e["taxa"], 0.03)
                e["socio"] = None
                e["part"] = min(1.0, e["part"] / 0.75)
                p["ativo"] = False
                revelar(e, p)
                mudar(e, rep=-6, felic=-12, saude=-8)
                conquistar(e, "licao")
                return f"🚨 {p['nome']} SUMIU! Sacou {brl(perda)} da conta da empresa e deixou {brl(v)} em dívidas no seu nome."
            agendar(e, 5, fuga)
        return f"Vocês apertaram as mãos. {p['nome']} agora é sócio(a) com 25% da empresa."

    def recusar(e):
        if not p["bom"]:
            def soube(e):
                revelar(e, p)
                p["ativo"] = False
                conquistar(e, "detetive")
                return f"📰 Você soube que {p['nome']} aplicou um golpe em outro empresário. Escapou por pouco!"
            agendar(e, 3, soube)
        else:
            def foi(e):
                mudar(e, felic=-2)
                return f"📰 {p['nome']} se associou a outra empresa, que está crescendo rápido. Será que você perdeu uma chance?"
            agendar(e, 4, foi)
        return f"Você agradeceu e recusou. {p['nome']} saiu meio contrariad{oa(p)}."
    return [(f"✅ Aceitar e investir {brl(v)}", aceitar), ("❌ Recusar", recusar)]


@evento("socio_decisao", "🤝 Hora de decidir sobre a sociedade", "", peso=0, cooldown=0)
def _(e):
    p = pessoa(e, "socio")
    return (f"Com o que você descobriu, vai entrar na sociedade com {p['nome']}?",
            _opcoes_socio(e, p, e.get("socio_valor", 3000)))


@evento("segredo_socio", "🤫 Um segredo sobre seu sócio", "Uma ex-funcionária do seu sócio quer falar com você…",
        cond=lambda e: e["socio"] is not None, peso=0.4, cooldown=12)
def _(e):
    p = e["pessoas"][e["socio"]]
    real = (not p["bom"]) == (random.random() < 0.8)

    def inv(e):
        e["caixa"] -= 800
        if not p["bom"]:
            e["seguinte"] = "desfazer_sociedade"
            conquistar(e, "detetive")
            return f"🔎 Auditoria confirmou: {p['nome']} estava desviando dinheiro aos poucos e planejava sumir!"
        return f"🔎 A auditoria não encontrou nada. {p['nome']} está limp{oa(p)}. Era fofoca."

    def confrontar(e):
        if not p["bom"]:
            if random.random() < 0.5:
                e["seguinte"] = "desfazer_sociedade"
                return f"{p['nome']} gaguejou, ficou vermelh{oa(p)}… e acabou admitindo que estava com problemas."
            p["bomba"] = e["mes"]
            return f"{p['nome']} jurou inocência, ofendid{oa(p)}. Mas ficou estranh{oa(p)} desde então…"
        mudar(e, rel=-3)
        return f"{p['nome']} ficou magoad{oa(p)} com a desconfiança, mas mostrou todos os extratos."

    def ignorar(e):
        return "Você preferiu acreditar no seu sócio e não tocou mais no assunto."
    boato = "está escondendo dívidas e já fez isso com outros sócios" if real or random.random() < .5 else "tem um passado complicado"
    return (f"Uma pessoa que trabalhou com **{p['nome']}** diz que ele(a) {boato}. Pode ser verdade… ou inveja.",
            [("🔎 Contratar auditoria (−R$ 800)", inv), ("🗣️ Confrontar cara a cara", confrontar), ("🙈 Ignorar", ignorar)])


@evento("desfazer_sociedade", "✂️ Desfazer a sociedade", "", peso=0, cooldown=0)
def _(e):
    p = e["pessoas"][e["socio"]]
    v = e.get("socio_valor", 3000)

    def sair(e):
        e["caixa"] += v * 0.5
        e["socio"] = None
        e["part"] = min(1.0, e["part"] / 0.75)
        p["ativo"] = False
        revelar(e, p)
        mudar(e, felic=+5, integ=+2)
        return f"Com provas na mão, você desfez a sociedade e recuperou {brl(v * 0.5)}. Ufa!"
    return (f"Você tem provas contra {p['nome']}. Vai desfazer a sociedade agora?",
            [("✂️ Desfazer e recuperar parte do dinheiro", sair)])


# --- 9. Amigo pede dinheiro
@evento("amigo_dinheiro", "🫂 Um amigo precisa de ajuda", "Seu celular toca. É um amigo antigo, com a voz embargada…",
        cond=lambda e: e["caixa"] > 2500, peso=1, cooldown=10)
def _(e):
    p = pessoa(e, "amigo")
    v = round(random.uniform(0.15, 0.35) * max(e["caixa"], 4000), -2)
    motivo = random.choice(["o aluguel atrasado", "uma cirurgia da mãe", "uma dívida que apertou", "pagar a faculdade do filho"])

    def emprestar(e, fr=1.0):
        val = v * fr
        e["caixa"] -= val
        if p["bom"]:
            e["flags"].add("ajudou_amigo")

            def paga(e):
                e["caixa"] += val * 1.1
                mudar(e, rel=+6, felic=+4)
                revelar(e, p)
                forcar(e, 4, "retribuicao")
                return f"🫂 {p['nome']} devolveu os {brl(val)} com um extra e um abraço apertado. Amizade de verdade."
            agendar(e, 4, paga)
        else:
            def some(e):
                revelar(e, p)
                mudar(e, rel=-6, felic=-6)
                conquistar(e, "licao")
                return f"📵 {p['nome']} não pagou, te bloqueou e foi visto(a) postando foto em viagem."
            agendar(e, 4, some)
        mudar(e, rel=+3, integ=+2)
        return f"Você emprestou {brl(val)} para {p['nome']}. Prometeu pagar em 4 meses."

    def recusar(e):
        if p["bom"]:
            mudar(e, rel=-3)
            return f"{p['nome']} entendeu, mas ficou chatead{oa(p)}."
        revelar(e, p)
        mudar(e, rep=-2, rel=-2)
        return f"{p['nome']} ficou furios{oa(p)} e começou a falar mal de você pela cidade. Mostrou quem era."
    return (f"**{p['nome']}** pede {brl(v)} emprestado para {motivo}. Promete devolver em 4 meses.",
            [(f"💵 Emprestar {brl(v)}", emprestar), (f"🤏 Emprestar metade", lambda e: emprestar(e, 0.5)),
             ("🙅 Recusar com jeito", recusar)])


@evento("retribuicao", "🌟 Quem planta, colhe", "Aquele amigo que você ajudou quer te apresentar alguém…",
        cond=lambda e: "ajudou_amigo" in e["flags"], peso=0, unico=True, cooldown=0)
def _(e):
    p = pessoa(e, "amigo")

    def aceitar(e):
        e["mercado"] *= 1.35
        mudar(e, rep=+5, rel=+5, felic=+5)
        return f"O cliente indicado por {p['nome']} fechou um contrato enorme! Mercado +35%."
    return (f"**{p['nome']}** não esqueceu sua ajuda e te indicou para o diretor de uma empresa grande.",
            [("🙏 Agradecer e aproveitar", aceitar)])


# --- 10. Amigo novo do sucesso
@evento("falso_amigo", "🥂 Os novos amigos do sucesso", "Você foi convidado para uma festa VIP numa cobertura…",
        cond=lambda e: e["fase_max"] >= 2, peso=1, unico=True)
def _(e):
    p = pessoa(e, "novo_amigo")
    v = round(max(5000, e["caixa"] * 0.3), -3)

    def investir(e):
        e["caixa"] -= v
        if p["bom"]:
            def ganha(e):
                e["caixa"] += v * 1.4
                return f"📈 O investimento indicado por {p['nome']} rendeu 40%. Nem todo mundo é golpista!"
            agendar(e, 4, ganha)
        else:
            def golpe(e):
                revelar(e, p)
                p["ativo"] = False
                mudar(e, felic=-8)
                conquistar(e, "licao")
                return f"📉 A 'cripto garantida' de {p['nome']} era pirâmide. Os {brl(v)} viraram pó, e {ele(p)} sumiu."
            agendar(e, 3, golpe)
        return f"Você colocou {brl(v)} no negócio de {p['nome']}."

    def recusar(e):
        if not p["bom"]:
            def soube(e):
                revelar(e, p)
                conquistar(e, "detetive")
                return f"📰 Saiu no jornal: o 'negócio garantido' de {p['nome']} era pirâmide financeira. Escapou!"
            agendar(e, 3, soube)
        mudar(e, saude=+2)
        return f"Você recusou com elegância. {p['nome']} continuou simpátic{oa(p)}… por enquanto."
    return (f"Na festa, **{p['nome']}** (que você nunca tinha visto até ficar bem de vida) jura que tem um investimento "
            f"em cripto que 'rende 10% ao mês, garantido'. Sugere você colocar {brl(v)}.",
            [(f"💸 Investir {brl(v)}", investir), ("🙅 Recusar", recusar)])


# --- 11–13. Amor
@evento("amor_conhecer", "💘 Um encontro inesperado", "Alguém sorriu para você no evento de ontem…",
        cond=lambda e: e["parceiro"] is None and "casado" not in e["flags"], peso=0.5, cooldown=18)
def _(e):
    p = pessoa(e, "amor")

    def sair(e):
        iniciar_namoro(e, p)
        forcar(e, 3, "amor_pedido")
        return f"Vocês saíram, riram a noite inteira… Começou um namoro com {p['nome']}! 💕"

    def foco(e):
        mudar(e, felic=-3)
        return "Você disse que agora o foco é a empresa. Será que perdeu alguém especial?"
    return (f"No evento, você conheceu **{p['nome']}, {p['idade']} anos**. Inteligente, engraçad{oa(p)}, "
            f"e parece muito interessad{oa(p)} em você… e no que você faz.",
            [("💌 Chamar para sair", sair), ("💼 Focar no trabalho", foco)])


@evento("amor_pedido", "💔 Uma conversa séria no jantar", "Seu amor quer conversar sobre 'o futuro de vocês'…",
        cond=lambda e: e["parceiro"] is not None, peso=0, cooldown=0)
def _(e):
    p = e["pessoas"][e["parceiro"]]
    v = round(max(4000, e["caixa"] * 0.35), -3)

    def dar(e):
        e["caixa"] -= v
        if p["bom"]:
            def ok(e):
                e["caixa"] += v
                mudar(e, felic=+8, rel=+5)
                revelar(e, p)
                forcar(e, 1, "casamento")
                return f"🌷 A loja de {p['nome']} deu certo, e {ele(p)} devolveu cada centavo. Que orgulho!"
            agendar(e, 5, ok)
        else:
            def fim(e):
                e["parceiro"] = None
                p["ativo"] = False
                revelar(e, p)
                mudar(e, felic=-15, saude=-10)
                conquistar(e, "licao")
                return f"💔 A 'loja' de {p['nome']} nunca existiu. Quando o dinheiro acabou, o amor também."
            agendar(e, 3, fim)
        mudar(e, felic=+5)
        return f"Você transferiu {brl(v)}. {p['nome']} te abraçou forte."

    def recusar(e):
        if p["bom"]:
            mudar(e, rel=+5, felic=+3)
            revelar(e, p)
            forcar(e, 2, "casamento")
            return f"{p['nome']} disse: 'Você tem razão, vou juntar aos poucos.' Vocês ficaram ainda mais próximos."
        e["parceiro"] = None
        p["ativo"] = False
        revelar(e, p)
        conquistar(e, "detetive")
        mudar(e, felic=-8)
        return f"{p['nome']} ficou fri{oa(p)}, sumiu por uma semana e terminou por mensagem. Doeu… mas foi melhor assim."

    def plano(e):
        mudar(e, saude=-3)
        if p["bom"]:
            mudar(e, rel=+8, conhec=+3)
            forcar(e, 2, "casamento")
            return f"Vocês montaram o plano juntos. {p['nome']} adorou sua ajuda: 'Você é a melhor coisa da minha vida.'"
        p["pistas"].append(f"{p['nome']} se irritou quando você pediu um plano de negócios.")
        forcar(e, 2, "amor_pedido")
        return f"{p['nome']} se irritou: 'Pra que tanta pergunta? Você não confia em mim?' Hmm…"
    return (f"**{p['nome']}** diz que quer abrir uma lojinha e pede {brl(v)} emprestado. *\"A gente é um time, né?\"*",
            [(f"💝 Dar o dinheiro", dar), ("🙅 Recusar com carinho", recusar),
             ("📝 Propor fazer um plano de negócios juntos", plano)])


@evento("casamento", "💍 O pedido!", "Você está com uma caixinha de veludo no bolso…",
        cond=lambda e: e["parceiro"] is not None and "casado" not in e["flags"], peso=0, cooldown=0)
def _(e):
    p = e["pessoas"][e["parceiro"]]

    def casar(e, separacao):
        e["flags"].add("casado")
        e["regime"] = "separacao" if separacao else "comunhao"
        e["atencao"] = min(100, e.get("atencao", 60) + 25)
        mudar(e, felic=+15, rel=+10, saude=+5)
        if p["bom"]:
            conquistar(e, "amor")
            return f"💍 Vocês se casaram! {p['nome']} é sua parceira de vida de verdade." if p["sexo"] == "F" else \
                   f"💍 Vocês se casaram! {p['nome']} é seu parceiro de vida de verdade."
        if not separacao:
            def divorcio(e):
                if e["parceiro"] != p["id"]:
                    return None
                perda = max(0, e["caixa"]) * 0.5
                e["caixa"] -= perda
                e["parceiro"] = None
                p["ativo"] = False
                e["flags"].discard("casado")
                revelar(e, p)
                mudar(e, felic=-20, saude=-15)
                return f"💔 {p['nome']} pediu o divórcio e levou {brl(perda)} na partilha. O interesse era o dinheiro."
            agendar(e, 6, divorcio)
        else:
            def sai(e):
                if e["parceiro"] != p["id"]:
                    return None
                e["parceiro"] = None
                p["ativo"] = False
                e["flags"].discard("casado")
                revelar(e, p)
                mudar(e, felic=-12)
                return f"💔 {p['nome']} pediu o divórcio, mas a separação de bens protegeu seu patrimônio."
            agendar(e, 6, sai)
        return f"💍 Vocês se casaram numa festa linda com {p['nome']}!"

    def esperar(e):
        mudar(e, felic=-2)
        return "Você guardou a caixinha. Ainda não é a hora."
    return (f"Depois de tudo, você pensa em pedir **{p['nome']}** em casamento. Seu advogado lembra: o regime de bens importa.",
            [("💍 Casar (comunhão parcial de bens)", lambda e: casar(e, False)),
             ("💍 Casar (separação total de bens)", lambda e: casar(e, True)), ("⏳ Esperar mais", esperar)])


# --- 14. Consultor
@evento("consultor", "📊 Um consultor bate à porta", "Recebeu um e-mail: 'Posso triplicar sua margem'…",
        cond=lambda e: e["mes"] > 4, peso=0.8, cooldown=14)
def _(e):
    p = pessoa(e, "consultor")
    v = round(1500 + receita_media(e) * 0.5, -2)

    def contratar_c(e):
        e["caixa"] -= v
        if p["bom"]:
            e["bonus_margem"] = min(0.15, e["bonus_margem"] + 0.04)
            e["mercado"] *= 1.15
            mudar(e, conhec=+10)
            revelar(e, p)
            return f"{p['nome']} reorganizou preços e processos. Margem +4%, clientes +15%. Valeu cada centavo!"
        mudar(e, conhec=+2)
        p["pistas"].append(f"O relatório de {p['nome']} parecia copiado da internet.")
        return f"{p['nome']} entregou 80 slides bonitos… e nenhuma ação prática."

    def inv(e):
        pista = investigar(e, p)
        e["seguinte"] = "consultor_decisao"
        return f"🔎 Você ligou para ex-clientes: \"{pista}\""
    e["consultor_v"] = v
    return (f"**{p['nome']}** oferece uma consultoria completa por {brl(v)}.",
            [(f"✅ Contratar (−{brl(v)})", contratar_c), ("🔎 Ligar para ex-clientes primeiro", inv),
             ("❌ Recusar", lambda e: "Você agradeceu e seguiu do seu jeito.")])


@evento("consultor_decisao", "📊 E a consultoria?", "", peso=0, cooldown=0)
def _(e):
    texto, opc = EVENTOS["consultor"]["montar"](e)
    return ("Agora que você sabe mais, contrata a consultoria?", [opc[0], opc[2]])


# --- 15. Investidor
@evento("investidor", "💼 Um investidor quer entrar", "Um fundo de investimento pediu seus números…",
        cond=lambda e: receita_media(e) > 8000 and e["part"] > 0.5, peso=0.8, cooldown=14)
def _(e):
    p = pessoa(e, "investidor")
    oferta = round(receita_media(e) * 10, -3)

    def aceitar(e, fatia=0.25):
        e["caixa"] += oferta
        e["part"] *= (1 - fatia)
        if p["bom"]:
            def rede(e):
                e["mercado"] *= 1.25
                mudar(e, rep=+5, conhec=+5)
                revelar(e, p)
                return f"💼 A rede de contatos de {p['nome']} abriu portas enormes. Mercado +25%."
            agendar(e, 3, rede)
        else:
            def pressao(e):
                revelar(e, p)
                mudar(e, felic=-10, saude=-8, rel=-5)
                e["mercado"] *= 0.9
                return f"💼 {p['nome']} exige cortes, demissões e metas absurdas. Você virou funcionário(a) da própria empresa."
            agendar(e, 4, pressao)
        return f"Entraram {brl(oferta)} no caixa. {p['nome']} agora tem {fatia:.0%} da empresa."

    def negociar(e):
        if random.random() < 0.5:
            return aceitar(e, 0.18)
        p["ativo"] = False
        return f"{p['nome']} achou sua contraproposta ousada demais e desistiu."
    return (f"**{p['nome']}** oferece {brl(oferta)} por 25% da sua empresa.",
            [("🤝 Aceitar", aceitar), ("🗣️ Negociar por 18%", negociar), ("❌ Recusar", lambda e: "Você preferiu crescer com as próprias pernas.")])


# --- 16. Concorrente desleal
@evento("concorrente", "🦈 Jogo sujo do concorrente", "Seu celular vibra sem parar: avaliações de 1 estrela…",
        cond=lambda e: e["mes"] > 5, peso=0.8, cooldown=12)
def _(e):
    p = pessoa(e, "concorrente")

    def transparencia(e):
        mudar(e, saude=-3, rep=+3 if e["integ"] >= 60 else 0, integ=+2)
        return "Você respondeu cada avaliação com educação e provas. Muitos clientes te defenderam."

    def falsas(e):
        mudar(e, integ=-15)
        e["mercado"] *= 1.1
        if random.random() < 0.35:
            def descoberta(e):
                mudar(e, rep=-20)
                e["mercado"] *= 0.8
                return "📰 Descobriram que você comprou avaliações falsas. Virou meme na cidade. Reputação despencou."
            agendar(e, 2, descoberta)
        return "Você comprou 200 avaliações 5 estrelas. Funcionou… por enquanto."

    def processar(e):
        e["caixa"] -= 2000
        if random.random() < (0.7 if not p["bom"] else 0.3):
            def ganha(e):
                e["caixa"] += 6000
                mudar(e, rep=+6)
                revelar(e, p)
                return f"⚖️ A Justiça provou que {p['nome']} estava por trás dos ataques. Indenização de R$ 6.000!"
            agendar(e, 3, ganha)
        return "Seu advogado entrou com uma ação por concorrência desleal."
    return (f"Alguém está espalhando avaliações falsas sobre você. Tudo indica que é **{p['nome']}**, seu concorrente.",
            [("🧾 Responder com transparência", transparencia), ("🤫 Comprar avaliações falsas também", falsas),
             ("⚖️ Processar (−R$ 2.000)", processar)])


# --- 17. Fiscalização
@evento("fiscalizacao", "👮 Fiscalização surpresa!", "Dois fiscais estão na porta pedindo para entrar…",
        cond=lambda e: e["mes"] > 6, peso=0.8, cooldown=14)
def _(e):
    sujo = "sonegou" in e["flags"] or e["integ"] < 50
    multa = round(max(2000, receita_media(e) * 0.8), -2)

    def docs(e):
        if sujo:
            e["caixa"] -= multa
            mudar(e, rep=-5)
            e["flags"].discard("sonegou")
            return f"Encontraram irregularidades. Multa de {brl(multa)}. Pelo menos agora está tudo regularizado."
        mudar(e, rep=+3, integ=+2)
        return "Tudo em ordem! Os fiscais até elogiaram sua organização."

    def jeitinho(e):
        mudar(e, integ=-25)
        e["caixa"] -= multa * 0.3
        if random.random() < 0.3:
            def escandalo(e):
                e["caixa"] -= multa * 3
                mudar(e, rep=-25)
                e["mercado"] *= 0.75
                return f"🚨 ESCÂNDALO! O fiscal foi preso e entregou quem pagou propina. Multa de {brl(multa * 3)} e sua imagem destruída."
            agendar(e, 2, escandalo)
        return f"Você 'deu um jeitinho' de {brl(multa * 0.3)}. Os fiscais foram embora sorrindo."
    return ("Os fiscais querem ver notas, alvarás e a contabilidade.",
            [("📂 Apresentar todos os documentos", docs), (f"🤝 'Dar um jeitinho' (propina)", jeitinho)])


# --- 18. Crise econômica
@evento("crise", "📉 Crise econômica!", "O noticiário só fala em juros altos e desemprego…",
        cond=lambda e: e["mes"] > 10, peso=0.5, cooldown=24)
def _(e):
    e["mercado"] *= 0.75

    def demitir_c(e):
        if e["func"] > 0:
            demitir(e, max(1, e["func"] // 3))
        mudar(e, integ=-3)
        return "Você cortou parte da equipe. Doeu, mas a empresa respira."

    def manter(e):
        e["vida_mult"] = 0.7
        mudar(e, felic=-6, rep=+6, rel=+4, integ=+4)

        def volta(e):
            e["vida_mult"] = 1.0
            e["mercado"] *= 1.15
            return "🌤️ A crise passou. Sua equipe, que você protegeu, está mais leal do que nunca."
        agendar(e, 4, volta)
        return "Você cortou o próprio salário para não demitir ninguém. A equipe nunca vai esquecer."

    def diversificar(e):
        custo = round(1000 + receita_media(e) * 0.3, -2)
        e["caixa"] -= custo
        if random.random() < 0.4 + e["conhec"] / 200:
            e["mercado"] *= 1.3
            return "Você encontrou um nicho que cresce na crise! Mercado se recuperou."
        return f"A diversificação custou {brl(custo)} e não decolou."
    return ("A economia afundou. Seus clientes estão comprando 25% menos.",
            [("✂️ Demitir parte da equipe", demitir_c), ("🛡️ Manter todos e cortar seu salário", manter),
             ("🧭 Diversificar para um novo nicho", diversificar)])


# --- 19. Golpe do Pix
@evento("golpe_pix", "📱 Mensagem urgente", "Chegou um áudio do 'seu fornecedor' com tom desesperado…",
        cond=lambda e: e["mes"] > 2, peso=0.7, unico=True)
def _(e):
    v = round(max(1500, receita_media(e) * 0.5), -2)

    def ligar(e):
        conquistar(e, "detetive")
        mudar(e, conhec=+5)
        return "Você ligou no número antigo do fornecedor: ele nunca mandou essa mensagem. Era golpe!"

    def pagar(e):
        e["caixa"] -= v
        mudar(e, felic=-5, conhec=+5)
        conquistar(e, "licao")
        return f"Você mandou {brl(v)}. Duas horas depois, o fornecedor de verdade ligou perguntando do pagamento… Era golpe."
    return (f"Seu 'fornecedor' manda mensagem de um número novo: 'Mudei de banco, paga os {brl(v)} nessa chave Pix nova, "
            "é urgente senão perco o desconto!'", [("📞 Ligar para o número antigo e confirmar", ligar), ("💸 Pagar logo", pagar)])


# --- 20. Mentor
@evento("mentor", "🧓 Um mentor aparece", "Um empresário famoso comentou no seu post…",
        cond=lambda e: e["conhec"] < 85, peso=0.6, cooldown=18)
def _(e):
    p = pessoa(e, "mentor")

    def aceitar(e):
        if p["bom"]:
            mudar(e, conhec=+15, rep=+4, saude=-3)
            revelar(e, p)
            return f"{p['nome']} te ensinou em um mês o que levaria anos. Conhecimento +15."
        mudar(e, conhec=+5, saude=-6, felic=-3)
        p["pistas"].append(f"{p['nome']} cobrou favores pessoais em troca dos conselhos.")
        return f"{p['nome']} ensinou umas coisas, mas cobrou favores e usou seu nome para se promover."
    return (f"**{p['nome']}**, dono(a) de um grupo de empresas, oferece mentoria gratuita em troca de você ajudar num projeto social.",
            [("🙏 Aceitar", aceitar), ("❌ Recusar", lambda e: "Você agradeceu. Agora não dá.")])


# --- 21. Pedido de aumento
@evento("aumento", "💬 Pedido de aumento", "Seu melhor funcionário pediu 'cinco minutinhos'…",
        cond=lambda e: e["func"] >= 2, peso=0.8, cooldown=10)
def _(e):
    def dar(e):
        e["extra_salario"] += 0.05
        e["mercado"] *= 1.05
        mudar(e, rep=+2, rel=+3)
        return "Aumento dado. A equipe ficou motivada e a produtividade subiu."

    def negar(e):
        if random.random() < 0.45:
            e["func"] -= 1
            e["mercado"] *= 0.95
            return "Ele pediu demissão e foi trabalhar para o concorrente, levando alguns clientes."
        mudar(e, felic=-2)
        return "Ele ficou, mas sem o mesmo brilho no olho."
    return ("O funcionário que mais vende pede 15% de aumento, dizendo que recebeu proposta do concorrente.",
            [("💰 Dar aumento", dar), ("🙅 Negar", negar)])


# --- 22. Viagem
@evento("viagem", "✈️ Convite para uma viagem", "Um convite dourado chegou pelo correio…",
        cond=lambda e: e["fase_max"] >= 2, peso=0.6, cooldown=14)
def _(e):
    v = round(4000 + receita_media(e) * 0.2, -3)

    def ir(e):
        e["caixa"] -= v
        mudar(e, felic=+15, saude=+12, rel=+5)
        if random.random() < 0.5:
            forcar(e, 1, "investidor")
            return "Viagem incrível! E na piscina você conheceu um investidor que pediu seu cartão…"
        return "Viagem incrível. Você voltou renovado(a)."
    return (f"Amigos ricos te chamaram para 10 dias em Fernando de Noronha. Sua parte: {brl(v)}.",
            [(f"🏝️ Ir (−{brl(v)})", ir), ("🏢 Ficar trabalhando", lambda e: (e.__setitem__("mercado", e["mercado"] * 1.05), "Você ficou e fechou uns negócios. Mas viu as fotos com inveja.")[1])])


# --- 23. Família
@evento("familia", "🎂 Família ou reunião?", "Dois compromissos marcados no mesmo dia…",
        cond=lambda e: e["rel"] < 95, peso=0.9, cooldown=8)
def _(e):
    quem = random.choice(["do seu filho", "da sua mãe", "do seu melhor amigo", "do seu pai"])

    def fam(e):
        e["mercado"] *= 0.96
        mudar(e, rel=+10, felic=+6, saude=+3)
        return "Você foi à festa. As risadas e o abraço valeram mais que qualquer contrato."

    def reuniao(e):
        e["mercado"] *= 1.1
        mudar(e, rel=-10, felic=-4)
        return "A reunião foi ótima e rendeu clientes. Mas alguém ficou te esperando…"
    return (f"O aniversário {quem} cai no mesmo horário da reunião com um cliente importante.",
            [("🎂 Ir ao aniversário", fam), ("💼 Ir à reunião", reuniao)])


# --- 24. Saúde
@evento("saude_alerta", "🩺 Seu corpo está pedindo socorro", "Você acordou com o coração disparado…", peso=0, cooldown=3)
def _(e):
    def ferias(e):
        e["mercado"] *= 0.9
        mudar(e, saude=+30, felic=+10, rel=+4)
        return "Duas semanas de descanso de verdade. Voltou com energia."

    def ignorar(e):
        if random.random() < 0.5:
            def internacao(e):
                e["caixa"] -= 3000
                e["mercado"] *= 0.8
                e["saude"] = 40
                return "🚑 Você desmaiou no escritório e ficou 1 semana internado(a). Hospital: R$ 3.000. Clientes sumiram."
            agendar(e, 1, internacao)
        mudar(e, saude=-5)
        return "Você tomou um remédio e voltou ao trabalho. Até quando?"
    return ("Insônia, ansiedade, dor no peito. O médico foi direto: 'Ou você para, ou o corpo vai te parar.'",
            [("🌴 Tirar 2 semanas de férias", ferias), ("💊 Ignorar e seguir", ignorar)])


# --- 25. Fornecedor sem nota
@evento("sem_nota", "📦 Fornecedor 'sem nota'", "Um fornecedor chegou com uma proposta 'por fora'…",
        cond=lambda e: e["mes"] > 3, peso=0.7, cooldown=14)
def _(e):
    def aceitar(e):
        e["bonus_margem"] = min(0.15, e["bonus_margem"] + 0.05)
        mudar(e, integ=-10)
        e["flags"].add("sonegou")
        return "Margem +5%… e um esqueleto no armário."
    return ("Ele oferece mercadoria 30% mais barata, mas sem nota fiscal.",
            [("🤫 Aceitar", aceitar), ("🧾 Recusar", lambda e: (mudar(e, integ=+3), "Você recusou. Seu contador te deu os parabéns.")[1])])


# --- 26. Contrato grande
@evento("contrato", "📜 Contrato milionário na mesa", "Uma multinacional quer marcar uma reunião…",
        cond=lambda e: e["fase_max"] >= 3, peso=0.8, cooldown=12)
def _(e):
    total = round(receita_media(e) * 4, -3)
    contratar_n = 3

    def aceitar(e):
        contratar(e, contratar_n)
        quebra = random.random() < 0.25
        for m in range(1, 7):
            def parcela(e, m=m):
                if quebra and m >= 3:
                    if m == 3:
                        mudar(e, felic=-8)
                        return "📜 O cliente do contrato milionário entrou em recuperação judicial e parou de pagar!"
                    return None
                e["caixa"] += total / 6 * 0.5
                return f"📜 Parcela {m}/6 do contrato grande: +{brl(total / 6 * 0.5)} de lucro." if m in (1, 6) else None
            agendar(e, m, parcela)
        mudar(e, rep=+6)
        return f"Contrato assinado! Você contratou {contratar_n} pessoas para dar conta."
    return (f"Contrato de {brl(total)} em 6 meses. Mas você precisa contratar {contratar_n} pessoas já.",
            [("✍️ Assinar", aceitar), ("❌ Recusar (risco alto)", lambda e: "Você preferiu não depender de um cliente só.")])


# --- 27. Proposta de compra
@evento("compra", "🏦 Querem comprar sua empresa", "Um grupo grande mandou um e-mail com o assunto 'Proposta'…",
        cond=lambda e: e["fase_max"] >= 3 and valor_empresa(e) > 100000, peso=0.5, cooldown=24)
def _(e):
    oferta = round(valor_empresa(e) * e["part"] * 1.3, -3)

    def vender(e):
        e["caixa"] += oferta
        e["fim"] = "venda"
        return f"Você vendeu tudo por {brl(oferta)}!"

    def recusar(e):
        mudar(e, rep=+4, felic=+3)
        return "Você recusou. 'Meu negócio não está à venda.' O mercado inteiro ficou sabendo."
    return (f"Um grupo oferece {brl(oferta)} pela sua parte na empresa. Se aceitar, sua jornada termina aqui com o dinheiro no bolso.",
            [(f"💰 Vender e se aposentar", vender), ("👑 Recusar e seguir rumo ao Império", recusar)])


# --- 28. Doação
@evento("doacao", "🎗️ Um pedido do coração", "Uma ONG do bairro pediu para falar com você…",
        cond=lambda e: e["caixa"] > 5000, peso=0.6, cooldown=12)
def _(e):
    v = round(max(1000, e["caixa"] * 0.05), -2)

    def doar(e):
        e["caixa"] -= v
        mudar(e, rep=+5, integ=+5, felic=+6, rel=+3)
        return "As crianças fizeram um cartaz de agradecimento com o nome da sua empresa. Você chorou um pouco."
    return (f"Uma ONG que ensina crianças precisa de {brl(v)} para não fechar.",
            [(f"💛 Doar {brl(v)}", doar), ("🙅 Agora não dá", lambda e: "Você explicou que o momento está difícil.")])



# ---------------------------------------------------------------- VIDA AFETIVA
def iniciar_namoro(e, p):
    e["parceiro"] = p["id"]
    e["namoro_desde"] = e["mes"]
    e["atencao"] = 70
    mudar(e, felic=+10, rel=+5)


def terminar_relacao(e, motivo, felic=-15, saude=-10):
    p = e["pessoas"].get(e["parceiro"]) if e["parceiro"] else None
    if not p:
        return ""
    txt = ""
    if "casado" in e["flags"]:
        if e.get("regime") == "comunhao":
            perda = max(0, e["caixa"]) * 0.3
            e["caixa"] -= perda
            txt = f" Na partilha de bens, foram {brl(perda)}."
        else:
            txt = " A separação de bens protegeu seu patrimônio."
        e["flags"].discard("casado")
    e["parceiro"] = None
    e["namoro_desde"] = None
    p["ativo"] = False
    mudar(e, felic=felic, saude=saude)
    log(e, f"💔 Fim do relacionamento com {p['nome']}: {motivo}.{txt}", p["id"])
    return f"💔 {p['nome']} e você terminaram: {motivo}.{txt}"


def vida_afetiva_mes(e, noticias):
    """Relacionamento precisa de atenção todo mês; casamento e filhos dão alegria mas exigem presença."""
    if not e["parceiro"]:
        return
    casado = "casado" in e["flags"]
    e["atencao"] = max(0, e.get("atencao", 60) - (10 if casado else 7) - (3 if e.get("filhos") else 0))
    if e["atencao"] >= 55:
        mudar(e, felic=+(3 if casado else 2), saude=+1)
        if casado and e["mes"] >= 60 and e["atencao"] > 70:
            conquistar(e, "amor_que_dura")
    elif e["atencao"] < 30:
        mudar(e, felic=-2)
        if not any(f["ev"] == "amor_atencao" for f in e["forcados"]) and "amor_atencao" not in e["usados"][-3:]:
            forcar(e, 1, "amor_atencao")
    if e["atencao"] <= 0:
        noticias.append(terminar_relacao(e, "você simplesmente não estava mais presente", felic=-18, saude=-12))
    if e.get("filhos"):
        mudar(e, felic=+2, saude=-1)


@evento("amor_atencao", "🥀 Seu relacionamento está esfriando", "Uma mensagem no celular: 'Precisamos conversar.'",
        cond=lambda e: e["parceiro"] is not None, peso=0, cooldown=2)
def _(e):
    p = e["pessoas"][e["parceiro"]]
    frase = random.choice(["Você casou com a empresa, não comigo.", "Eu me sinto sozinh{a} mesmo com você do lado.",
                           "Quando foi a última vez que a gente conversou sem você olhar o celular?"]).format(a=oa(p))

    def jantar(e):
        custo = round(300 + receita_media(e) * 0.03, -2)
        e["caixa"] -= custo
        e["atencao"] = min(100, e["atencao"] + 45)
        mudar(e, felic=+6, rel=+4)
        return f"Jantar especial, celular desligado ({brl(custo)}). Vocês riram como no começo. ❤️"

    def prometer(e):
        e["atencao"] = min(100, e["atencao"] + 15)
        e["mercado"] *= 0.97
        return "Você prometeu chegar mais cedo. Agora precisa cumprir: lembre de cuidar da família nos próximos meses."

    def ignorar(e):
        e["atencao"] = max(0, e["atencao"] - 15)
        mudar(e, rel=-5)
        if random.random() < 0.45:
            forcar(e, 2, "traicao")
        return "Você respondeu 'depois a gente fala' e voltou para a planilha."
    return (f"**{p['nome']}** desabafa: *\"{frase}\"*",
            [("🍷 Jantar especial, só vocês dois", jantar), ("🤞 Prometer mudar", prometer), ("💼 'Agora não dá'", ignorar)])


@evento("traicao", "💔 Uma descoberta que dói", "Uma notificação acendeu no celular errado, na hora errada…",
        cond=lambda e: e["parceiro"] is not None and (e.get("atencao", 60) < 40 or not e["pessoas"][e["parceiro"]]["bom"])
        and e["mes"] - (e.get("namoro_desde") or e["mes"]) >= 4, peso=0.5, cooldown=24)
def _(e):
    p = e["pessoas"][e["parceiro"]]
    e["flags"].add("traido")
    mudar(e, saude=-22, felic=-18)
    carente = p["bom"]  # pessoa boa que se afastou por solidão x pessoa interesseira

    def perdoar(e):
        if carente:
            e["atencao"] = 55
            mudar(e, felic=+5, rel=+3)
            revelar(e, p)
            return (f"Vocês conversaram a noite inteira. {p['nome']} se arrependeu de verdade: se sentia invisível. "
                    "A confiança vai demorar, mas vocês decidiram recomeçar.")
        e["atencao"] = 40
        forcar(e, 4, "traicao")
        return f"Você perdoou. {p['nome']} jurou que nunca mais… e pediu um presente caro para 'selar a paz'."

    def terminar(e):
        if not carente:
            revelar(e, p)
            conquistar(e, "detetive")
        return terminar_relacao(e, "traição", felic=-5, saude=-3)

    def terapia(e):
        e["caixa"] -= 600
        mudar(e, saude=+15, felic=+5, conhec=+3)
        p["pistas"].append(f"Na terapia você percebeu: {p['nome']} " +
                           ("se afastou porque você também se afastou." if carente else "sempre esteve mais perto do seu dinheiro do que de você."))
        e["seguinte"] = "traicao_decisao"
        return "A terapeuta te ajudou a enxergar com mais clareza o que aconteceu."
    origem = "com alguém do trabalho, nas suas longas ausências" if carente else "com outra pessoa, enquanto pedia presentes caros a você"
    return (f"Você descobriu que **{p['nome']}** estava se envolvendo {origem}. O chão sumiu. (Saúde emocional −22)",
            [("🤝 Perdoar e tentar de novo", perdoar), ("🚪 Terminar", terminar), ("🛋️ Fazer terapia antes de decidir (−R$ 600)", terapia)])


@evento("traicao_decisao", "💔 E agora?", "", peso=0, cooldown=0)
def _(e):
    _, opc = EVENTOS["traicao"]["montar"](e)
    e["flags"].add("traido")
    mudar(e, saude=+22, felic=+18)  # a dor já foi contada no evento anterior
    return ("Com a cabeça mais no lugar, o que você decide?", opc[:2])


@evento("bebe", "👶 Uma notícia que muda tudo", "Seu amor está com um sorriso diferente hoje…",
        cond=lambda e: e["parceiro"] is not None and e.get("filhos", 0) < 3 and e.get("atencao", 60) >= 40
        and e["mes"] - (e.get("namoro_desde") or e["mes"]) >= 8, peso=0.5, cooldown=18)
def _(e):
    p = e["pessoas"][e["parceiro"]]

    def ter(e):
        e["filhos"] = e.get("filhos", 0) + 1
        e["atencao"] = min(100, e["atencao"] + 20)
        mudar(e, felic=+20, rel=+12, saude=-8)
        conquistar(e, "familia_formada")
        if p["bom"]:
            revelar(e, p)
        log(e, f"👶 Nasceu seu {'primeiro filho' if e['filhos'] == 1 else str(e['filhos']) + 'º filho'}!", p["id"])
        return ("👶 Daqui a alguns meses chega um bebê! Noites sem dormir, custo de vida maior, "
                "e um amor que você nem sabia que existia.")

    def esperar(e):
        if p["bom"]:
            mudar(e, rel=-3)
            return f"Vocês conversaram e decidiram esperar a empresa se estabilizar. {p['nome']} entendeu, mas ficou pensativ{oa(p)}."
        e["atencao"] = max(0, e["atencao"] - 20)
        return f"{p['nome']} ficou fri{oa(p)}: 'Então eu não sou prioridade, né?'"
    return (f"**{p['nome']}** diz que quer ter um filho com você. Isso vai mudar suas prioridades para sempre.",
            [("👶 Vamos ter um filho!", ter), ("⏳ Ainda não é a hora", esperar)])


@evento("filho_momento", "🧸 Coisas de pai e mãe", "Tem um desenho colado na geladeira com seu nome…",
        cond=lambda e: e.get("filhos", 0) > 0, peso=1.1, cooldown=5)
def _(e):
    cena = random.choice([
        ("Hoje é a apresentação de dança na escola, no mesmo horário da reunião com o maior cliente do ano.",
         "🎭 Ir à apresentação", "💼 Ir à reunião"),
        ("Seu filho acordou com febre de 39 °C na madrugada, e amanhã cedo você tem uma visita importante.",
         "🌡️ Ficar em casa cuidando", "📅 Manter a visita e pedir ajuda"),
        ("No jantar, seu filho pergunta: 'Por que você nunca está em casa?'",
         "🤗 Tirar o fim de semana inteiro para ele", "📱 Explicar que é pelo futuro dele"),
        ("A escola chamou: as notas caíram e o professor quer conversar com os pais.",
         "🏫 Ir à reunião da escola", "📧 Responder por e-mail"),
    ])
    texto, sim, nao = cena

    def presente(e):
        e["mercado"] *= 0.96
        e["atencao"] = min(100, e.get("atencao", 60) + 15)
        mudar(e, rel=+10, felic=+8, saude=+3)
        return "Você estava lá. O olhar dele ao te ver vai ficar na sua memória para sempre."

    def ausente(e):
        e["mercado"] *= 1.06
        mudar(e, rel=-8, felic=-6)
        e["atencao"] = max(0, e.get("atencao", 60) - 10)
        return "O trabalho rendeu. Mas à noite ele já estava dormindo quando você chegou."
    return (texto, [(sim, presente), (nao, ausente)])


@evento("pretendente", "🎩 Um(a) pretendente encantador(a)", "Chegou um buquê sem cartão no seu escritório…",
        cond=lambda e: e["parceiro"] is None and e["fase_max"] >= 3, peso=0.6, cooldown=24)
def _(e):
    p = nova_pessoa(e, "amor", forcar_bom=random.random() < 0.25)
    pergunta = random.choice(["quanto sua empresa fatura", "se você tem imóveis no seu nome",
                              "se você pensa em viajar para Dubai em breve"])

    def sair(e):
        iniciar_namoro(e, p)
        forcar(e, 3, "amor_pedido")
        return f"Vocês começaram a sair. {p['nome']} é encantador{'a' if p['sexo'] == 'F' else ''}… e caro{'a' if p['sexo'] == 'F' else ''}."

    def devagar(e):
        p["pistas"].append(f"Logo no 1º encontro, {p['nome']} perguntou {pergunta}.")
        mudar(e, saude=+2)
        return f"Você preferiu ir devagar e observar. Anotou que {p['nome']} perguntou {pergunta} logo de cara."
    return (f"Desde que você ficou famoso(a) na cidade, **{p['nome']}, {p['idade']} anos**, "
            f"apareceu do nada: presentes, elogios, convites. No primeiro café, perguntou {pergunta}.",
            [("💘 Se deixar levar", sair), ("🧐 Ir devagar e observar", devagar)])


@evento("amigo_dificil", "🫂 Um amigo no fundo do poço", "Faz tempo que seu amigo não posta nada…",
        cond=lambda e: e["mes"] > 6, peso=0.7, cooldown=16)
def _(e):
    p = pessoa(e, "amigo")
    drama = random.choice(["perdeu o emprego e está em depressão", "se separou e não consegue sair da cama",
                           "perdeu o pai e está sem chão"])

    def presente(e):
        e["mercado"] *= 0.95
        mudar(e, rel=+12, integ=+4, felic=+4, saude=-3)
        if p["bom"]:
            revelar(e, p)
            e["flags"].add("ajudou_amigo")
            forcar(e, 6, "retribuicao")
        return f"Você passou dias ao lado de {p['nome']}. Não resolveu tudo, mas {ele(p)} disse: 'Você salvou minha vida.'"

    def mensagem(e):
        mudar(e, rel=-6)
        return f"Você mandou um 'força, amigo!' e voltou ao trabalho. {p['nome']} visualizou e não respondeu."
    return (f"**{p['nome']}** {drama}. Não pediu dinheiro, só precisa de alguém por perto. Mas este mês a empresa está a mil.",
            [("🫂 Estar presente de verdade", presente), ("📱 Mandar uma mensagem de apoio", mensagem)])


# --- 29. Mês tranquilo
@evento("mes_tranquilo", "☕ Um mês tranquilo", "Parece que vem aí um mês calmo… será?", peso=0.7, cooldown=3)
def _(e):
    return ("Pela primeira vez em muito tempo, sobrou uma tarde livre. O que fazer?",
            [("📖 Ler um livro de negócios", lambda e: (mudar(e, conhec=+4), "Você anotou três ideias que vai testar.")[1]),
             ("🍝 Jantar com amigos", lambda e: (mudar(e, rel=+5, felic=+3), "Boas conversas, boa comida. Recarregou.")[1]),
             ("🧮 Revisar as contas", lambda e: (e.__setitem__("caixa", e["caixa"] + receita_media(e) * 0.05),
                                               f"Você achou assinaturas esquecidas e economizou {brl(receita_media(e) * 0.05)}.")[1])])


# ---------------------------------------------------------------- INTERFACE
CSS_VIDA = """<style>
.vida-hero{background:linear-gradient(135deg,#1b1240 0%,#3b1d6e 50%,#b8860b 130%);color:#fff;border-radius:18px;
  padding:22px 24px;margin-bottom:14px;box-shadow:0 8px 30px rgba(59,29,110,.35)}
.vida-hero h2{margin:0;font-size:1.7rem;color:#ffd34d}.vida-hero p{margin:.3rem 0 0;opacity:.9}
.vida-top{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;
  background:linear-gradient(90deg,#1b1240,#3b1d6e);color:#fff;border-radius:14px;padding:12px 16px;margin-bottom:10px}
.vida-top b{color:#ffd34d}.vida-chip{display:inline-block;padding:3px 10px;border-radius:999px;margin:2px;font-size:.85rem;
  background:rgba(128,128,128,.15)}
.vida-chip.up{background:rgba(46,160,67,.18);color:#2ea043}.vida-chip.down{background:rgba(218,54,51,.16);color:#da3633}
.vida-ev{border:2px solid #b8860b;border-radius:16px;padding:18px 20px;margin:8px 0 12px;
  background:linear-gradient(180deg,rgba(184,134,11,.10),rgba(184,134,11,.02))}
.vida-ev h3{margin:0 0 .4rem;color:#b8860b}
.vida-teaser{border-left:4px solid #8a5cf6;padding:8px 12px;border-radius:6px;background:rgba(138,92,246,.10);margin:8px 0}
.vida-conq{border-radius:12px;padding:10px;text-align:center;min-height:92px}
.vida-conq.on{background:linear-gradient(135deg,#ffd34d33,#b8860b33);border:1px solid #b8860b}
.vida-conq.off{background:rgba(128,128,128,.08);border:1px dashed rgba(128,128,128,.4);opacity:.7}
</style>"""


def vida_hall():
    hall = S.get("vida_hall", [])
    if not hall:
        return
    st.markdown("#### 🏛️ Hall da Fama")
    for i, h in enumerate(sorted(hall, key=lambda h: -h["pts"])[:10], 1):
        medalha = {1: "🥇", 2: "🥈", 3: "🥉"}.get(i, f"{i}º")
        st.markdown(f"{medalha} **{h['pts']} pts**: {h['empresa']} ({h['ramo']}) · {h['fase']} · "
                    f"{h['meses']} meses · *{h['titulo']}* · {h['fim']}")


def vida_setup():
    st.markdown(CSS_VIDA, unsafe_allow_html=True)
    st.markdown("""<div class="vida-hero"><h2>👑 A VIDA É UM JOGO</h2>
    <p><b>Do Zero ao Império.</b> Construa seu império. Descubra em quem confiar. Escolha quem você quer ser.</p>
    <p style="font-size:.9rem;opacity:.8">Você começa com R$ 3.000, um computador velho e muita coragem.</p></div>""",
                unsafe_allow_html=True)
    legado = S.get("vida_legado", 0)
    if legado:
        st.success(f"🧬 **Experiência de vidas passadas:** você começa com **+{legado} de conhecimento**.")
    with st.form("vida_setup"):
        empresa = st.text_input("Nome da sua empresa", placeholder="Ex.: Silva Soluções, Sabor da Vila, NovaTech…", max_chars=40)
        ramo = st.radio("Em que ramo você vai empreender?", list(RAMOS),
                        captions=[RAMOS[r]["desc"] for r in RAMOS])
        if st.form_submit_button("🚀 Começar minha vida", type="primary"):
            S.vida = novo_jogo_vida(S.get("usuario", "Você"), empresa.strip() or "Minha Empresa", ramo, legado)
            st.rerun()
    vida_hall()


def vida_topo(e):
    ano, mes = (e["mes"] - 1) // 12 + 1, (e["mes"] - 1) % 12 + 1
    fogo = f" · 🔥 {e['seq_lucro']} meses no lucro" if e["seq_lucro"] >= 2 else ""
    st.markdown(f"""<div class="vida-top"><span>🏢 <b>{e['empresa']}</b> · {e['ramo']}</span>
      <span>📅 Ano {ano}, mês {mes}{fogo}</span><span>{FASES[e['fase_max']][0]}</span></div>""", unsafe_allow_html=True)
    c = st.columns(4)
    c[0].metric("💵 Caixa", brl(e["caixa"]))
    c[1].metric("🏦 Dívida", brl(e["divida"]), f"{e['taxa'] * 100:.1f}% a.m." if e["divida"] else None,
                delta_color="off")
    c[2].metric("📈 Faturamento/mês", brl(e["hist_receita"][-1] if e["hist_receita"] else 0))
    c[3].metric("💎 Patrimônio", brl(patrimonio(e)))
    cols = st.columns(3)
    for i, k in enumerate(IND):
        cols[i % 3].progress(e[k] / 100, text=f"{NOME_IND[k]}: **{e[k]:.0f}**")
    if e["parceiro"]:
        p = e["pessoas"][e["parceiro"]]
        a = e.get("atencao", 60)
        estado = "💍 Casamento" if "casado" in e["flags"] else "❤️ Namoro"
        filhos = f" · 👶 {e['filhos']} filho(s)" if e.get("filhos") else ""
        alerta = " ⚠️ precisa de você!" if a < 30 else ""
        st.progress(a / 100, text=f"{estado} com {p['nome']}{filhos} · atenção ao relacionamento: **{a:.0f}**{alerta}")
    elif e.get("filhos"):
        st.caption(f"👶 {e['filhos']} filho(s)")
    if e["fase_max"] < len(FASES) - 1:
        nome, fat, pat = FASES[e["fase_max"] + 1]
        rm, pt = receita_media(e), patrimonio(e)
        st.caption(f"🎯 **Próxima fase: {nome}**. Precisa de faturamento médio de {brl(fat)} e patrimônio de {brl(max(pat, 0))}.")
        a, b = st.columns(2)
        a.progress(min(1.0, max(0.0, rm / fat)), text=f"Faturamento {rm / fat:.0%}")
        b.progress(min(1.0, max(0.0, pt / pat)) if pat > 0 else 1.0, text=f"Patrimônio {max(0, pt) / pat:.0%}" if pat > 0 else "Patrimônio ✔")
    else:
        st.caption("🏰 **Você construiu um IMPÉRIO.** Agora é cuidar do que importa: vida plena e legado.")


def vida_acao(e):
    ev = EVENTOS[e["prox"]]
    if ev["teaser"]:
        st.markdown(f"<div class='vida-teaser'>🔮 <b>Neste mês:</b> {ev['teaser']}</div>", unsafe_allow_html=True)
    st.markdown(f"### 📅 Mês {e['mes']}: onde você vai colocar sua energia?")
    acoes = acoes_disponiveis(e)
    cols = st.columns(2)
    for i, (rot, desc, custo, chave) in enumerate(acoes):
        with cols[i % 2]:
            if st.button(rot, key=f"vida_a_{chave}_{e['mes']}", width="stretch",
                         type="primary" if chave in ("vender", "marketing") else "secondary"):
                e["acao_txt"] = fazer_acao(e, chave, custo)
                e["ev"] = montar_evento(e, e["prox"])
                e["resultados"] = []
                e["etapa"] = "evento"
                st.rerun()
            st.caption(desc)

    lim = ESTRUTURAS[e["estrutura"]][1]
    with st.expander(f"👥 Equipe: {e['func']} de {lim} funcionário(s) · {ESTRUTURAS[e['estrutura']][0]}"):
        cap = capacidade(e)
        st.write(f"Capacidade de atendimento: **{brl(cap)}/mês** · Demanda de clientes: **{brl(e['mercado'])}/mês**")
        if e["mercado"] > cap * 1.05:
            st.warning("Tem mais cliente do que você dá conta! Contrate para não perder reputação.")
        st.caption(f"Cada funcionário custa {brl(e['r']['salario'] * (1 + e['extra_salario']))}/mês e aumenta a "
                   f"capacidade em {brl(e['r']['capf'])}. Contratar custa meio salário; demitir custa 1,2 salário.")
        c1, c2 = st.columns(2)
        livre = lim - e["func"]
        if livre > 0:
            n = c1.number_input("Quantos contratar?", 1, livre, 1, key=f"vida_nc_{e['mes']}")
            if c1.button("➕ Contratar", key=f"vida_c_{e['mes']}"):
                contratar(e, int(n))
                st.rerun()
        else:
            c1.info("Sem espaço. Mude para uma estrutura maior.")
        if e["func"] > 0:
            n2 = c2.number_input("Quantos demitir?", 1, e["func"], 1, key=f"vida_nd_{e['mes']}")
            if c2.button("➖ Demitir", key=f"vida_d_{e['mes']}"):
                demitir(e, int(n2))
                st.rerun()

    with st.expander(f"🏦 Banco: limite disponível {brl(limite_credito(e))}"):
        c1, c2 = st.columns(2)
        lim_c = int(limite_credito(e) // 500 * 500)
        if lim_c >= 500:
            v = c1.number_input("Pegar empréstimo (3,5% a.m.)", 500, lim_c, min(5000, lim_c), 500, key=f"vida_emp_{e['mes']}")
            if c1.button("💳 Pegar", key=f"vida_pe_{e['mes']}"):
                pegar_emprestimo(e, float(v))
                st.rerun()
        else:
            c1.info("O banco não libera mais crédito para você agora.")
        if e["divida"] > 0 and e["caixa"] > 0:
            maxp = int(min(e["divida"], e["caixa"]))
            v2 = c2.number_input("Pagar dívida", 1, max(1, maxp), max(1, maxp), key=f"vida_am_{e['mes']}")
            if c2.button("✅ Pagar", key=f"vida_pa_{e['mes']}"):
                amortizar(e, float(v2))
                st.rerun()


def vida_evento(e):
    if e.get("acao_txt"):
        st.info(f"✔️ {e['acao_txt']}")
    for r in e["resultados"]:
        st.success(r)
    ev = e["ev"]
    st.markdown(f"<div class='vida-ev'><h3>{ev['titulo']}</h3></div>", unsafe_allow_html=True)
    st.markdown(ev["texto"])
    for i, (rot, fn) in enumerate(ev["opcoes"]):
        if st.button(rot, key=f"vida_o_{ev['id']}_{i}_{e['mes']}_{len(e['resultados'])}", width="stretch"):
            res = fn(e)
            if res:
                e["resultados"].append(res)
                log(e, f"{ev['titulo']}: {res}")
            nxt = e.pop("seguinte", None)
            if nxt and not e["fim"]:
                e["ev"] = montar_evento(e, nxt)
            elif e["fim"]:
                e["etapa"] = "fim"
            else:
                fechar_mes(e)
            st.rerun()
    st.caption("Não existe resposta certa. Toda escolha tem vantagens, riscos e consequências, e algumas só aparecem meses depois.")


def chips_variacao(e, antes):
    chips = []
    for k in IND:
        d = e[k] - antes[k]
        if abs(d) >= 1:
            chips.append(f"<span class='vida-chip {'up' if d > 0 else 'down'}'>{NOME_IND[k]} {d:+.0f}</span>")
    d = patrimonio(e) - antes["patrimonio"]
    chips.append(f"<span class='vida-chip {'up' if d >= 0 else 'down'}'>💎 Patrimônio {'+' if d >= 0 else ''}{brl(d)}</span>")
    return "".join(chips)


def vida_relatorio(e):
    r = e["relatorio"]
    for cid in e["novas_conq"]:
        st.toast(f"🏆 Conquista: {CONQUISTAS[cid][0]}", icon="🏆")
    if e["fase_max"] > r["fase_antes"]:
        st.balloons()
        st.success(f"## 🚀 NOVA FASE: {FASES[e['fase_max']][0]}!")
    if e["resultados"]:
        for res in e["resultados"]:
            st.info(res)
    st.markdown(f"### 📊 Fechamento do mês {r['mes']}")
    cor = "#2ea043" if r["resultado"] >= 0 else "#da3633"
    st.markdown(f"<div style='font-size:1.9rem;font-weight:800;color:{cor}'>"
                f"{'Lucro' if r['resultado'] >= 0 else 'Prejuízo'} de {brl(abs(r['resultado']))}</div>", unsafe_allow_html=True)
    st.markdown(f"""
| Mês {r['mes']} | Valor |
|---|---|
| 📈 Faturamento | **{brl(r['receita'])}** |
| ➖ Custos do produto/serviço | {brl(r['receita'] - r['lucro_bruto'])} |
| 🏢 Custo fixo (aluguel, contas) | {brl(r['fixo'])} |
| 👥 Salários | {brl(r['salarios'])} |
| 🏦 Juros | {brl(r['juros'])} |
| 🏠 Seu custo de vida | {brl(r['vida'])} |
""")
    st.markdown(chips_variacao(e, r["antes"]), unsafe_allow_html=True)
    if e["noticias"]:
        st.markdown("#### 📰 Aconteceu neste mês")
        for n in e["noticias"]:
            st.markdown(f"- {n}")
    if e["novas_conq"]:
        st.markdown("#### 🏆 Conquistas desbloqueadas")
        for cid in e["novas_conq"]:
            st.markdown(f"**{CONQUISTAS[cid][0]}**: {CONQUISTAS[cid][1]}")

    if e["mes"] > 60 and not e["avaliacao5"]:
        e["avaliacao5"] = True
        pts = pontuacao(e)
        st.markdown("---\n## 🎂 Avaliação dos seus 5 anos")
        cols = st.columns(5)
        for c, (k, v) in zip(cols, dimensoes(e).items()):
            c.metric(k, v)
        st.success(f"Pontuação de vida: **{pts}/1000**: *{titulo_vida(pts)}*. A jornada continua rumo ao Império!")

    ev = EVENTOS[e["prox"]]
    if ev["teaser"]:
        st.markdown(f"<div class='vida-teaser'>🔮 <b>Próximo mês:</b> {ev['teaser']}</div>", unsafe_allow_html=True)
    if st.button(f"▶️ Viver o mês {e['mes']}", type="primary", key=f"vida_prox_{e['mes']}", width="stretch"):
        e["novas_conq"] = []
        e["resultados"] = []
        e["acao_txt"] = ""
        e["etapa"] = "acao"
        st.rerun()


def vida_registrar_fim(e):
    if e.get("registrado"):
        return
    e["registrado"] = True
    pts = pontuacao(e)
    fim = {"falencia": "💥 Faliu", "venda": "💰 Vendeu a empresa", "aposentou": "🌅 Aposentou"}.get(e["fim"], e["fim"])
    S.setdefault("vida_hall", []).append(dict(pts=pts, empresa=e["empresa"], ramo=e["ramo"], fase=FASES[e["fase_max"]][0],
                                              meses=e["mes"] - 1, titulo=titulo_vida(pts), fim=fim))
    S.vida_legado = min(30, S.get("vida_legado", 0) + max(2, (e["mes"] - 1) // 6))


def vida_fim(e):
    vida_registrar_fim(e)
    pts = pontuacao(e)
    if e["fim"] == "falencia":
        st.error(f"## 💥 Falência no mês {e['mes'] - 1}\nO caixa acabou e o banco não empresta mais. "
                 "Mas todo grande empreendedor já quebrou pelo menos uma vez.")
    elif e["fim"] == "venda":
        st.balloons()
        st.success(f"## 💰 Você vendeu a empresa e saiu com {brl(e['caixa'] - e['divida'])}!")
    else:
        st.success("## 🌅 Você encerrou essa vida e deixou seu legado.")
    st.markdown(f"### Pontuação de vida: {pts}/1000: *{titulo_vida(pts)}*")
    cols = st.columns(5)
    for c, (k, v) in zip(cols, dimensoes(e).items()):
        c.metric(k, v)
    piores = sorted(dimensoes(e).items(), key=lambda x: x[1])[:2]
    st.info("📚 **Lição desta vida:** " + " e ".join(f"{k} ficou em {v}" for k, v in piores) +
            ". Dinheiro sozinho não é sucesso; o jogo mede a vida inteira.")
    st.success(f"🧬 Na próxima vida você começa com **+{S.get('vida_legado', 0)} de conhecimento** pela experiência acumulada.")
    if st.button("🔄 Viver uma nova vida", type="primary", key="vida_nova"):
        S.vida = None
        st.rerun()
    vida_hall()


def persona_prompt(e, p):
    pap = PAPEIS[p["papel"]]
    hist = [t for (_, t, pid) in e["diario"] if pid == p["id"]][-6:]
    return (f"Você é {p['nome']}, {p['idade']} anos, personagem do jogo de simulação 'A Vida É um Jogo'. "
            f"Seu papel na vida do jogador: {pap['titulo']}.\n"
            f"SUA VERDADEIRA PERSONALIDADE (segredo, nunca revele diretamente): {pap['b'] if p['bom'] else pap['r']}.\n"
            f"O jogador se chama {e['jogador']}, dono(a) da empresa '{e['empresa']}' ({e['ramo']}). Mês {e['mes']} da jornada. "
            f"Caixa da empresa: {brl(e['caixa'])}. Fase: {FASES[e['fase_max']][0]}.\n"
            f"O que já aconteceu entre vocês: {' | '.join(hist) or 'vocês se conheceram há pouco.'}\n"
            "REGRAS: responda em português do Brasil, no máximo 3 frases curtas, como uma pessoa real conversando por "
            "mensagem. Nunca saia do personagem e nunca diga que é uma IA. Se você é desonesto(a), deixe pistas SUTIS "
            "(pressa, promessas exageradas, fugir de perguntas sobre documentos, desviar para dinheiro), mas nunca confesse. "
            "Se é honesto(a), seja transparente, admita riscos e limites, e às vezes diga verdades desconfortáveis.")


def vida_pessoas(e):
    if not e["pessoas"]:
        st.info("Você ainda não conheceu ninguém.")
        return
    st.caption("💬 Converse com as pessoas (a IA dá vida a cada uma) e observe as atitudes. "
               "Ninguém é totalmente previsível. Descubra em quem confiar!")
    pessoas = sorted(e["pessoas"].values(), key=lambda p: (not p["ativo"], -p["conheceu"]))
    for p in pessoas:
        if p["revelado"]:
            status = "✅ Provou ser confiável" if p["bom"] else "🚩 Mostrou quem realmente é"
        else:
            status = "❔ Confiabilidade desconhecida"
        ativo = "" if p["ativo"] else " · 🚪 saiu da sua vida"
        with st.expander(f"{p['nome']}, {p['idade']} anos · {PAPEIS[p['papel']]['titulo']} · {status}{ativo}"):
            if p["pistas"]:
                st.markdown("**🔎 O que você descobriu:**\n" + "\n".join(f"- {x}" for x in p["pistas"]))
            for papel_msg, txt in e["chats"][p["id"]]:
                with st.chat_message("user" if papel_msg == "user" else "assistant",
                                     avatar=None if papel_msg == "user" else "🧑"):
                    st.write(txt)
            if not p["ativo"]:
                continue
            if not S.get("groq_key"):
                st.caption("Entre com uma chave Groq para conversar.")
                continue
            with st.form(f"vida_chat_{p['id']}", clear_on_submit=True):
                msg = st.text_input(f"Mensagem para {p['nome']}", placeholder="Pergunte algo, negocie, observe…")
                if st.form_submit_button("💬 Enviar") and msg.strip():
                    hist = [{"role": "system", "content": persona_prompt(e, p)}]
                    for papel_msg, txt in e["chats"][p["id"]][-10:]:
                        hist.append({"role": papel_msg, "content": txt})
                    hist.append({"role": "user", "content": msg.strip()})
                    try:
                        with st.spinner(f"{p['nome']} está digitando…"):
                            resp = groq_chat(hist)
                        e["chats"][p["id"]] += [("user", msg.strip()), ("assistant", resp.strip())]
                    except Exception:
                        st.error("Não consegui falar com a IA agora. Tente de novo.")
                    st.rerun()


def vida_diario(e):
    for mes, txt, _ in reversed(e["diario"][-80:]):
        st.markdown(f"**Mês {mes}** · {txt}")


def vida_conquistas(e):
    cols = st.columns(3)
    for i, (cid, (nome, desc)) in enumerate(CONQUISTAS.items()):
        on = cid in e["conquistas"]
        cols[i % 3].markdown(f"<div class='vida-conq {'on' if on else 'off'}'><b>{nome if on else '🔒 ' + nome.split(' ', 1)[1]}</b>"
                             f"<br><small>{desc}</small></div>", unsafe_allow_html=True)
        cols[i % 3].write("")


def jogo_vida():
    if not S.get("vida"):
        vida_setup()
        return
    e = S.vida
    st.markdown(CSS_VIDA, unsafe_allow_html=True)
    if e["etapa"] == "fim":
        vida_fim(e)
        return
    vida_topo(e)
    n_conq = len(e["conquistas"])
    abas = st.tabs(["🎮 Jogar", f"👥 Pessoas ({sum(p['ativo'] for p in e['pessoas'].values())})", "📜 Diário",
                    f"🏆 Conquistas ({n_conq}/{len(CONQUISTAS)})"])
    with abas[0]:
        {"acao": vida_acao, "evento": vida_evento, "relatorio": vida_relatorio}[e["etapa"]](e)
    with abas[1]:
        vida_pessoas(e)
    with abas[2]:
        vida_diario(e)
    with abas[3]:
        vida_conquistas(e)
        st.write("")
        if st.button("🌅 Encerrar esta vida e entrar no Hall da Fama", key="vida_aposentar"):
            e["fim"] = "aposentou"
            e["etapa"] = "fim"
            st.rerun()


# =====================================================================
# JOGOS EM HTML LIVRE (raciocínio e alta tecnologia)
# =====================================================================
UTIL_JS = r"""
const $ = id => document.getElementById(id);
function lerRecorde(n){ try { return +localStorage.getItem(n) || 0; } catch (e) { return 0; } }
function salvarRecorde(n, v, menorMelhor){ const r = lerRecorde(n);
  if (!r || (menorMelhor ? v < r : v > r)) { try { localStorage.setItem(n, v); } catch (e) {} return v; } return r; }
function embaralhar(a){ for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random()*(i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function fmtTempo(s){ s = Math.floor(s); return String(Math.floor(s/60)).padStart(2, '0') + ':' + String(s % 60).padStart(2, '0'); }
let AC = null, mudo = false;
function audio(){ if (!AC) { try { AC = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) {} }
  if (AC && AC.state === 'suspended') AC.resume(); return AC; }
function bip(freq = 440, dur = 0.08, tipo = 'square', vol = 0.06, desliza = 0){ const a = audio(); if (!a || mudo) return;
  const o = a.createOscillator(), g = a.createGain(); o.type = tipo; o.frequency.setValueAtTime(freq, a.currentTime);
  if (desliza) o.frequency.exponentialRampToValueAtTime(Math.max(30, freq + desliza), a.currentTime + dur);
  g.gain.setValueAtTime(vol, a.currentTime); g.gain.exponentialRampToValueAtTime(0.0001, a.currentTime + dur);
  o.connect(g); g.connect(a.destination); o.start(); o.stop(a.currentTime + dur + 0.02); }
function ruido(dur = 0.3, vol = 0.12){ const a = audio(); if (!a || mudo) return;
  const n = Math.floor(a.sampleRate*dur), b = a.createBuffer(1, n, a.sampleRate), d = b.getChannelData(0);
  for (let i = 0; i < n; i++) d[i] = (Math.random()*2 - 1) * (1 - i/n) ** 2;
  const s = a.createBufferSource(), g = a.createGain(); s.buffer = b; g.gain.value = vol; s.connect(g); g.connect(a.destination); s.start(); }
function acorde(notas, dur = 0.12){ notas.forEach((f, i) => setTimeout(() => bip(f, dur, 'triangle', 0.07), i*90)); }
function vibrar(ms){ try { navigator.vibrate && navigator.vibrate(ms); } catch (e) {} }
"""

CSS_LIVRE = """
*{box-sizing:border-box}
html,body{margin:0;background:transparent;font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#e8ecf8;
  -webkit-user-select:none;user-select:none;-webkit-tap-highlight-color:transparent}
.painel{max-width:560px;margin:0 auto;background:linear-gradient(180deg,#171c2e,#0f1322);border-radius:18px;padding:14px;
  box-shadow:0 10px 30px rgba(0,0,0,.35)}
.barra{display:flex;flex-wrap:wrap;gap:8px;align-items:center;justify-content:space-between;margin-bottom:10px}
.info{display:flex;gap:10px;flex-wrap:wrap}.tag{background:#263052;border-radius:999px;padding:5px 11px;font-size:14px;font-weight:600}
button{font:inherit;cursor:pointer;border:none;border-radius:10px;padding:9px 13px;background:#2c3659;color:#fff;font-weight:700;
  touch-action:manipulation}
button:hover{background:#3a4673}button:active{transform:translateY(1px)}
button.on{background:#ffb02e;color:#1a1a1a}button.pri{background:#4f7cff}
.msg{text-align:center;font-weight:800;font-size:18px;min-height:26px;margin:8px 0}
.ok{color:#5be08a}.ruim{color:#ff6b6b}
@keyframes treme{0%,100%{transform:translateX(0)}25%{transform:translateX(-6px)}75%{transform:translateX(6px)}}
.treme{animation:treme .25s}
"""


def pagina_livre(corpo: str, js: str, css: str = "", head: str = "") -> str:
    return ("<!doctype html><html><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>" + head +
            "<style>" + CSS_LIVRE + css + "</style></head><body>" + corpo +
            "<script>" + UTIL_JS + "\n" + js + "</script></body></html>")


def jogo_html(pagina: str, altura: int):
    if hasattr(st, "iframe"):
        st.iframe(pagina, height=altura)
    else:
        components.html(pagina, height=altura, scrolling=False)


# ---------------------------------------------------------------- SUDOKU
SUDOKU_CSS = """
#grade{display:grid;grid-template-columns:repeat(9,1fr);aspect-ratio:1;width:100%;max-width:480px;margin:0 auto;
  border:3px solid #8fa6ff;border-radius:8px;overflow:hidden;background:#8fa6ff;gap:1px}
.cel{background:#1d2440;display:flex;align-items:center;justify-content:center;font-size:clamp(16px,5.2vw,26px);
  font-weight:700;color:#8fd3ff;cursor:pointer;position:relative}
.cel.dada{color:#fff}.cel.rel{background:#252e52}.cel.mesmo{background:#33406e}.cel.sel{background:#4f7cff;color:#fff}
.cel.erro{color:#ff6b6b}.cel.bd{border-right:2px solid #8fa6ff}.cel.bb{border-bottom:2px solid #8fa6ff}
.notas{display:grid;grid-template-columns:repeat(3,1fr);width:100%;height:100%;font-size:clamp(7px,2vw,11px);color:#9aa8d8;
  font-weight:600}.notas span{display:flex;align-items:center;justify-content:center}
#teclado{display:grid;grid-template-columns:repeat(9,1fr);gap:5px;max-width:480px;margin:10px auto 0}
#teclado button{padding:10px 0;font-size:20px}#teclado small{display:block;font-size:10px;opacity:.6}
.acoes{display:flex;gap:6px;justify-content:center;margin-top:8px;flex-wrap:wrap}
"""
SUDOKU_HTML = """<div class="painel"><div class="barra"><div class="info"><span class="tag">⏱️ <b id="tempo">00:00</b></span>
<span class="tag">❌ Erros <b id="erros">0</b>/3</span></div><div class="info">
<button data-n="Fácil">Fácil</button><button data-n="Médio" class="on">Médio</button><button data-n="Difícil">Difícil</button></div></div>
<div id="grade"></div><div class="msg" id="msg"></div><div id="teclado"></div>
<div class="acoes"><button id="bnota">✏️ Notas: não</button><button id="bapaga">⌫ Apagar</button><button id="bdica">💡 Dica</button>
<button id="bnovo" class="pri">🔄 Novo jogo</button></div></div>"""
SUDOKU_JS = r"""
let sol, dado, val, notas, sel = -1, modoNota = false, erros = 0, t0 = 0, fim = false, nivel = 'Médio';
const REMOVER = {'Fácil': 38, 'Médio': 47, 'Difícil': 54};
function pode(g, i, n){ const r = Math.floor(i/9), c = i % 9;
  for (let k = 0; k < 9; k++) if (g[r*9 + k] === n || g[k*9 + c] === n) return false;
  const br = r - r % 3, bc = c - c % 3;
  for (let a = 0; a < 3; a++) for (let b = 0; b < 3; b++) if (g[(br + a)*9 + bc + b] === n) return false; return true; }
function preencher(g){ const i = g.indexOf(0); if (i < 0) return true;
  for (const n of embaralhar([1,2,3,4,5,6,7,8,9])) if (pode(g, i, n)) { g[i] = n; if (preencher(g)) return true; g[i] = 0; } return false; }
function contar(g, lim){ let melhor = -1, ops = null;
  for (let i = 0; i < 81; i++) if (!g[i]) { const o = []; for (let n = 1; n <= 9; n++) if (pode(g, i, n)) o.push(n);
    if (!o.length) return 0; if (melhor < 0 || o.length < ops.length) { melhor = i; ops = o; if (o.length === 1) break; } }
  if (melhor < 0) return 1; let t = 0;
  for (const n of ops) { g[melhor] = n; t += contar(g, lim - t); g[melhor] = 0; if (t >= lim) break; } return t; }
function novo(){ const g = Array(81).fill(0); preencher(g); sol = g.slice(); const p = g.slice(); let rem = 0;
  for (const i of embaralhar([...Array(81).keys()])) { if (rem >= REMOVER[nivel]) break; const v = p[i]; p[i] = 0;
    if (contar(p.slice(), 2) !== 1) p[i] = v; else rem++; }
  dado = p.map(v => v > 0); val = p.slice(); notas = Array.from({length: 81}, () => new Set());
  sel = -1; erros = 0; fim = false; t0 = performance.now(); $('msg').textContent = ''; desenhar(); }
function relac(i, j){ const ri = Math.floor(i/9), ci = i % 9, rj = Math.floor(j/9), cj = j % 9;
  return ri === rj || ci === cj || (Math.floor(ri/3) === Math.floor(rj/3) && Math.floor(ci/3) === Math.floor(cj/3)); }
function desenhar(){
  const g = $('grade'); g.innerHTML = '';
  for (let i = 0; i < 81; i++) {
    const d = document.createElement('div'), c = i % 9, r = Math.floor(i/9);
    d.className = 'cel' + (dado[i] ? ' dada' : '') + (c === 2 || c === 5 ? ' bd' : '') + (r === 2 || r === 5 ? ' bb' : '');
    if (sel >= 0) { if (i === sel) d.classList.add('sel'); else if (val[sel] && val[i] === val[sel]) d.classList.add('mesmo'); else if (relac(i, sel)) d.classList.add('rel'); }
    if (val[i]) { d.textContent = val[i]; if (val[i] !== sol[i]) d.classList.add('erro'); }
    else if (notas[i].size) { const n = document.createElement('div'); n.className = 'notas';
      for (let k = 1; k <= 9; k++) { const s = document.createElement('span'); s.textContent = notas[i].has(k) ? k : ''; n.appendChild(s); } d.appendChild(n); }
    d.onclick = () => { sel = i; desenhar(); }; g.appendChild(d);
  }
  const tc = $('teclado'); tc.innerHTML = '';
  for (let n = 1; n <= 9; n++) { const b = document.createElement('button'), resta = 9 - val.filter((v, i) => v === n && v === sol[i]).length;
    b.innerHTML = n + '<small>' + (resta > 0 ? resta : '✔') + '</small>'; b.disabled = resta <= 0; b.style.opacity = resta > 0 ? 1 : .35;
    b.onclick = () => digitar(n); tc.appendChild(b); }
  $('erros').textContent = erros; $('bnota').textContent = '✏️ Notas: ' + (modoNota ? 'sim' : 'não'); $('bnota').classList.toggle('on', modoNota);
}
function digitar(n){
  if (fim || sel < 0 || dado[sel]) return;
  if (modoNota) { notas[sel].has(n) ? notas[sel].delete(n) : notas[sel].add(n); bip(700, .03, 'sine'); desenhar(); return; }
  val[sel] = n; notas[sel].clear();
  if (n !== sol[sel]) { erros++; bip(160, .2, 'sawtooth'); vibrar(80); $('grade').classList.add('treme'); setTimeout(() => $('grade').classList.remove('treme'), 260);
    if (erros >= 3) { fim = true; $('msg').innerHTML = '<span class="ruim">💥 3 erros! Fim de jogo.</span>'; val = sol.slice(); } }
  else { bip(880, .05, 'triangle'); for (let j = 0; j < 81; j++) if (relac(sel, j)) notas[j].delete(n); }
  if (val.every((v, i) => v === sol[i]) && !fim) { fim = true; const t = (performance.now() - t0)/1000;
    const rec = salvarRecorde('rec_sudoku_' + nivel, Math.floor(t), true);
    $('msg').innerHTML = '<span class="ok">🎉 Resolvido em ' + fmtTempo(t) + '! Recorde (' + nivel + '): ' + fmtTempo(rec) + '</span>'; acorde([523, 659, 784, 1046]); }
  desenhar();
}
$('bnota').onclick = () => { modoNota = !modoNota; desenhar(); };
$('bapaga').onclick = () => { if (sel >= 0 && !dado[sel] && !fim) { val[sel] = 0; notas[sel].clear(); desenhar(); } };
$('bdica').onclick = () => { if (fim) return; let alvo = sel >= 0 && !dado[sel] && val[sel] !== sol[sel] ? sel : -1;
  if (alvo < 0) { const v = [...Array(81).keys()].filter(i => val[i] !== sol[i]); if (!v.length) return; alvo = v[Math.floor(Math.random()*v.length)]; }
  sel = alvo; const ant = modoNota; modoNota = false; digitar(sol[alvo]); modoNota = ant; desenhar(); };
$('bnovo').onclick = novo;
document.querySelectorAll('[data-n]').forEach(b => b.onclick = () => { nivel = b.dataset.n;
  document.querySelectorAll('[data-n]').forEach(x => x.classList.toggle('on', x === b)); novo(); });
addEventListener('keydown', e => {
  if (e.key >= '1' && e.key <= '9') digitar(+e.key);
  else if (['Backspace', 'Delete', '0'].includes(e.key)) $('bapaga').onclick();
  else if (e.key.toLowerCase() === 'n') $('bnota').onclick();
  else if (e.key.startsWith('Arrow')) { e.preventDefault(); if (sel < 0) sel = 0;
    const d = {ArrowUp: -9, ArrowDown: 9, ArrowLeft: -1, ArrowRight: 1}[e.key]; sel = (sel + d + 81) % 81; desenhar(); }
});
setInterval(() => { if (!fim) $('tempo').textContent = fmtTempo((performance.now() - t0)/1000); }, 500);
novo();
"""

# ---------------------------------------------------------------- SENHA (Mastermind)
SENHA_CSS = """
.linha{display:flex;align-items:center;gap:10px;justify-content:center;padding:5px;border-radius:12px;margin:3px 0}
.linha.atual{background:#263052;box-shadow:0 0 0 2px #4f7cff inset}
.num{width:22px;text-align:right;opacity:.5;font-size:13px}
.pino{width:34px;height:34px;border-radius:50%;background:#2a3150;box-shadow:inset 0 2px 5px rgba(0,0,0,.5);cursor:pointer;
  transition:transform .12s}.pino.cor{box-shadow:inset 0 -3px 6px rgba(0,0,0,.35),0 2px 4px rgba(0,0,0,.4)}
.pino:hover{transform:scale(1.08)}
.fb{display:grid;grid-template-columns:repeat(3,10px);gap:3px;width:40px}
.fb i{width:10px;height:10px;border-radius:50%;background:#2a3150}.fb i.p{background:#111;border:1.5px solid #ddd}.fb i.b{background:#fff}
#paleta{display:flex;gap:8px;justify-content:center;flex-wrap:wrap;margin:10px 0}
#paleta .pino{width:42px;height:42px}
#segredo .pino{width:30px;height:30px}
"""
SENHA_HTML = """<div class="painel"><div class="barra"><div class="info"><span class="tag">🎯 Tentativa <b id="tent">1</b>/10</span>
<span class="tag">🏆 Vitórias <b id="vit">0</b></span></div><div class="info">
<button data-m="Fácil">Fácil</button><button data-m="Normal" class="on">Normal</button><button data-m="Difícil">Difícil</button></div></div>
<div class="linha" id="segredo"></div><div id="tab"></div><div class="msg" id="msg"></div>
<div id="paleta"></div><div class="acoes" style="display:flex;gap:8px;justify-content:center">
<button id="bconf" class="pri">✅ Conferir</button><button id="bapaga">⌫ Apagar</button><button id="bnovo">🔄 Nova senha</button></div></div>"""
SENHA_JS = r"""
const CORES = ['#e53935', '#1e88e5', '#43a047', '#fdd835', '#8e24aa', '#fb8c00', '#00acc1', '#ec407a'];
const MODOS = {'Fácil': {pos: 4, cores: 6, rep: false}, 'Normal': {pos: 4, cores: 6, rep: true}, 'Difícil': {pos: 5, cores: 8, rep: true}};
let modo = 'Normal', cfg, segredo, tent, atual, fim, vit = lerRecorde('rec_senha_vit');
function novo(){ cfg = MODOS[modo]; const base = [...Array(cfg.cores).keys()];
  segredo = cfg.rep ? Array.from({length: cfg.pos}, () => Math.floor(Math.random()*cfg.cores)) : embaralhar(base).slice(0, cfg.pos);
  tent = []; atual = []; fim = false; $('msg').textContent = ''; desenhar(); }
function avaliar(c){ let p = 0, b = 0; const rs = [], rc = [];
  for (let i = 0; i < cfg.pos; i++) { if (c[i] === segredo[i]) p++; else { rs.push(segredo[i]); rc.push(c[i]); } }
  for (const x of rc) { const k = rs.indexOf(x); if (k >= 0) { b++; rs.splice(k, 1); } } return [p, b]; }
function pino(cor, onclick){ const d = document.createElement('div'); d.className = 'pino' + (cor != null ? ' cor' : '');
  if (cor != null) d.style.background = 'radial-gradient(circle at 35% 30%, #fff8, ' + CORES[cor] + ' 45%)'; if (onclick) d.onclick = onclick; return d; }
function desenhar(){
  const s = $('segredo'); s.innerHTML = '<span class="num">🔒</span>';
  segredo.forEach(c => s.appendChild(fim ? pino(c) : Object.assign(pino(null), {textContent: ''})));
  if (!fim) [...s.querySelectorAll('.pino')].forEach(p => { p.style.display = 'flex'; p.style.alignItems = 'center'; p.style.justifyContent = 'center'; p.textContent = '?'; });
  const t = $('tab'); t.innerHTML = '';
  for (let r = 0; r < 10; r++) {
    const l = document.createElement('div'); l.className = 'linha' + (r === tent.length && !fim ? ' atual' : '');
    l.innerHTML = '<span class="num">' + (r + 1) + '</span>';
    const linha = r < tent.length ? tent[r].c : r === tent.length ? atual : [];
    for (let i = 0; i < cfg.pos; i++) l.appendChild(pino(linha[i] ?? null, r === tent.length && !fim ? () => { atual.splice(i, 1); desenhar(); } : null));
    const fb = document.createElement('div'); fb.className = 'fb';
    if (r < tent.length) { const [p, b] = tent[r].f; for (let i = 0; i < cfg.pos; i++) { const x = document.createElement('i'); x.className = i < p ? 'p' : i < p + b ? 'b' : ''; fb.appendChild(x); } }
    l.appendChild(fb); t.appendChild(l);
  }
  const pa = $('paleta'); pa.innerHTML = '';
  for (let c = 0; c < cfg.cores; c++) pa.appendChild(pino(c, () => { if (fim || atual.length >= cfg.pos) return;
    if (!cfg.rep && atual.includes(c)) return; atual.push(c); bip(500 + c*80, .05, 'sine'); desenhar(); }));
  $('tent').textContent = Math.min(10, tent.length + 1); $('vit').textContent = vit;
}
$('bconf').onclick = () => { if (fim || atual.length < cfg.pos) { $('tab').classList.add('treme'); setTimeout(() => $('tab').classList.remove('treme'), 260); return; }
  const f = avaliar(atual); tent.push({c: atual.slice(), f}); atual = [];
  if (f[0] === cfg.pos) { fim = true; vit++; salvarRecorde('rec_senha_vit', vit); acorde([523, 659, 784, 1046]);
    $('msg').innerHTML = '<span class="ok">🎉 Quebrou a senha em ' + tent.length + ' tentativa(s)!</span>'; }
  else if (tent.length >= 10) { fim = true; bip(150, .4, 'sawtooth'); $('msg').innerHTML = '<span class="ruim">🔒 Acabaram as tentativas. Veja a senha acima.</span>'; }
  else bip(300 + f[0]*150, .08, 'triangle');
  desenhar(); };
$('bapaga').onclick = () => { atual.pop(); desenhar(); };
$('bnovo').onclick = novo;
document.querySelectorAll('[data-m]').forEach(b => b.onclick = () => { modo = b.dataset.m;
  document.querySelectorAll('[data-m]').forEach(x => x.classList.toggle('on', x === b)); novo(); });
addEventListener('keydown', e => { if (e.key >= '1' && e.key <= '8') { const c = +e.key - 1; if (c < cfg.cores) $('paleta').children[c].onclick(); }
  else if (e.key === 'Enter') $('bconf').onclick(); else if (e.key === 'Backspace') $('bapaga').onclick(); });
novo();
"""

# ---------------------------------------------------------------- TORRE DE HANÓI
HANOI_CSS = """
#torres{display:flex;justify-content:space-between;gap:8px;height:300px;margin-top:6px}
.torre{flex:1;position:relative;display:flex;flex-direction:column-reverse;align-items:center;padding-bottom:14px;cursor:pointer;
  border-radius:12px;transition:background .15s}
.torre:hover{background:rgba(255,255,255,.04)}.torre.alvo{background:rgba(79,124,255,.12)}
.torre::before{content:'';position:absolute;bottom:14px;width:10px;height:85%;background:linear-gradient(#8a6a4a,#5c4330);border-radius:6px}
.torre::after{content:'';position:absolute;bottom:0;width:96%;height:14px;background:#5c4330;border-radius:6px}
.disco{height:26px;border-radius:13px;margin-top:3px;z-index:1;transition:transform .15s;box-shadow:inset 0 -4px 0 rgba(0,0,0,.25)}
.disco.sobe{transform:translateY(-40px)}
"""
HANOI_HTML = """<div class="painel"><div class="barra"><div class="info"><span class="tag">🔁 Movimentos <b id="mov">0</b></span>
<span class="tag">🎯 Mínimo <b id="min">7</b></span></div><div class="info"><span>Discos:</span>
<select id="qtd" style="font:inherit;border-radius:8px;padding:6px;background:#2c3659;color:#fff;border:none"></select></div></div>
<div id="torres"></div><div class="msg" id="msg"></div>
<div style="display:flex;gap:8px;justify-content:center"><button id="bnovo" class="pri">🔄 Recomeçar</button><button id="bsol">🤖 Ver solução</button></div></div>"""
HANOI_JS = r"""
const CORES = ['#ff4d6d', '#ff9f1c', '#ffd60a', '#43aa8b', '#00b4d8', '#4f7cff', '#9d4edd', '#f15bb5'];
let n = 4, pinos, sel = null, mov = 0, fim, auto = null;
for (let k = 3; k <= 8; k++) $('qtd').innerHTML += '<option ' + (k === 4 ? 'selected' : '') + '>' + k + '</option>';
function novo(){ if (auto) clearInterval(auto); auto = null; n = +$('qtd').value; pinos = [[...Array(n).keys()].reverse(), [], []];
  sel = null; mov = 0; fim = false; $('msg').textContent = ''; $('min').textContent = 2 ** n - 1; desenhar(); }
function desenhar(){ const t = $('torres'); t.innerHTML = '';
  pinos.forEach((p, i) => { const d = document.createElement('div'); d.className = 'torre' + (sel !== null && sel !== i ? ' alvo' : '');
    p.forEach((disco, j) => { const x = document.createElement('div'); x.className = 'disco' + (sel === i && j === p.length - 1 ? ' sobe' : '');
      x.style.width = (30 + disco*(62/n)) + '%'; x.style.background = CORES[disco % 8]; d.appendChild(x); });
    d.onclick = () => clicar(i); t.appendChild(d); });
  $('mov').textContent = mov; }
function mover(a, b){ const pa = pinos[a], pb = pinos[b];
  if (!pa.length || (pb.length && pb[pb.length - 1] < pa[pa.length - 1])) return false;
  pb.push(pa.pop()); mov++; bip(300 + pb[pb.length - 1]*60, .07, 'triangle'); return true; }
function verificar(){ if (pinos[2].length === n) { fim = true;
    const otimo = mov === 2 ** n - 1; acorde([523, 659, 784, 1046]);
    $('msg').innerHTML = '<span class="ok">🎉 Conseguiu com ' + mov + ' movimentos' + (otimo ? ' (PERFEITO! ⭐⭐⭐)' : '') + '</span>'; } }
function clicar(i){ if (fim || auto) return;
  if (sel === null) { if (pinos[i].length) { sel = i; bip(600, .03, 'sine'); } }
  else if (sel === i) sel = null;
  else { if (!mover(sel, i)) { bip(140, .15, 'sawtooth'); $('torres').classList.add('treme'); setTimeout(() => $('torres').classList.remove('treme'), 260); } sel = null; verificar(); }
  desenhar(); }
$('bnovo').onclick = novo; $('qtd').onchange = novo;
$('bsol').onclick = () => { novo(); const passos = []; (function h(k, a, b, c){ if (!k) return; h(k - 1, a, c, b); passos.push([a, c]); h(k - 1, b, a, c); })(n, 0, 1, 2);
  let i = 0; auto = setInterval(() => { if (i >= passos.length) { clearInterval(auto); auto = null; fim = true;
    $('msg').innerHTML = '<span class="ok">🤖 Essa é a solução perfeita: ' + (2 ** n - 1) + ' movimentos.</span>'; return; }
    mover(...passos[i++]); desenhar(); }, Math.max(80, 600 - n*60)); };
addEventListener('keydown', e => { if (['1', '2', '3'].includes(e.key)) clicar(+e.key - 1); });
novo();
"""

# ---------------------------------------------------------------- QUEBRA-CABEÇA DESLIZANTE
DESLIZA_CSS = """
#tab{position:relative;width:100%;max-width:440px;aspect-ratio:1;margin:0 auto;background:#0b0f1d;border-radius:14px;padding:6px}
.peca{position:absolute;display:flex;align-items:center;justify-content:center;border-radius:10px;font-weight:800;color:#fff;
  font-size:clamp(18px,6vw,34px);cursor:pointer;transition:left .12s ease-out,top .12s ease-out;text-shadow:0 2px 4px rgba(0,0,0,.4);
  box-shadow:inset 0 -5px 0 rgba(0,0,0,.25)}
.peca.certa{outline:2px solid rgba(255,255,255,.5);outline-offset:-4px}
"""
DESLIZA_HTML = """<div class="painel"><div class="barra"><div class="info"><span class="tag">🔁 <b id="mov">0</b> mov.</span>
<span class="tag">⏱️ <b id="tempo">00:00</b></span><span class="tag">🏆 <b id="rec">—</b></span></div><div class="info">
<button data-t="3">3×3</button><button data-t="4" class="on">4×4</button><button data-t="5">5×5</button></div></div>
<div id="tab"></div><div class="msg" id="msg"></div><div style="text-align:center"><button id="bnovo" class="pri">🔀 Embaralhar</button></div></div>"""
DESLIZA_JS = r"""
let N = 4, tab, mov, t0, fim, comecou;
function novo(){ tab = [...Array(N*N).keys()].map(i => (i + 1) % (N*N)); let vazio = N*N - 1, ant = -1;
  for (let k = 0; k < 60*N*N; k++) { const viz = vizinhos(vazio).filter(v => v !== ant); const v = viz[Math.floor(Math.random()*viz.length)];
    [tab[vazio], tab[v]] = [tab[v], tab[vazio]]; ant = vazio; vazio = v; }
  if (resolvido()) return novo();
  mov = 0; fim = false; comecou = false; $('msg').textContent = ''; const r = lerRecorde('rec_desliza_' + N); $('rec').textContent = r ? r + ' mov.' : '—'; montar(); }
function vizinhos(i){ const r = Math.floor(i/N), c = i % N, v = []; if (r > 0) v.push(i - N); if (r < N - 1) v.push(i + N); if (c > 0) v.push(i - 1); if (c < N - 1) v.push(i + 1); return v; }
function resolvido(){ return tab.every((v, i) => v === (i + 1) % (N*N)); }
function montar(){ const t = $('tab'); t.innerHTML = '';
  for (let v = 1; v < N*N; v++) { const d = document.createElement('div'); d.className = 'peca'; d.id = 'p' + v; d.textContent = v;
    const h = 210 + (v - 1)/(N*N - 1)*150; d.style.background = 'linear-gradient(135deg,hsl(' + h + ',75%,58%),hsl(' + (h + 25) + ',70%,42%))';
    d.onclick = () => clicar(tab.indexOf(v)); t.appendChild(d); } posicionar(); }
function posicionar(){ const tam = 100/N;
  tab.forEach((v, i) => { if (!v) return; const d = $('p' + v); d.style.width = d.style.height = 'calc(' + tam + '% - 6px)';
    d.style.left = 'calc(' + (i % N)*tam + '% + 3px)'; d.style.top = 'calc(' + Math.floor(i/N)*tam + '% + 3px)';
    d.classList.toggle('certa', v === i + 1); }); $('mov').textContent = mov; }
function clicar(i){ if (fim) return; const z = tab.indexOf(0), ri = Math.floor(i/N), ci = i % N, rz = Math.floor(z/N), cz = z % N;
  if (ri !== rz && ci !== cz) { bip(140, .08, 'sawtooth'); return; }
  const passo = ri === rz ? (ci > cz ? 1 : -1) : (ri > rz ? N : -N); let atual = z;
  while (atual !== i) { const prox = atual + passo; tab[atual] = tab[prox]; tab[prox] = 0; atual = prox; mov++; }
  if (!comecou) { comecou = true; t0 = performance.now(); }
  bip(420 + Math.random()*80, .04, 'triangle'); posicionar();
  if (resolvido()) { fim = true; const t = (performance.now() - t0)/1000; const r = salvarRecorde('rec_desliza_' + N, mov, true);
    $('rec').textContent = r + ' mov.'; acorde([523, 659, 784, 1046]);
    $('msg').innerHTML = '<span class="ok">🎉 Montado com ' + mov + ' movimentos em ' + fmtTempo(t) + '!</span>'; } }
addEventListener('keydown', e => { const z = tab.indexOf(0), r = Math.floor(z/N), c = z % N;
  const alvo = {ArrowLeft: c < N - 1 ? z + 1 : -1, ArrowRight: c > 0 ? z - 1 : -1, ArrowUp: r < N - 1 ? z + N : -1, ArrowDown: r > 0 ? z - N : -1}[e.key];
  if (alvo !== undefined) { e.preventDefault(); if (alvo >= 0) clicar(alvo); } });
document.querySelectorAll('[data-t]').forEach(b => b.onclick = () => { N = +b.dataset.t;
  document.querySelectorAll('[data-t]').forEach(x => x.classList.toggle('on', x === b)); novo(); });
$('bnovo').onclick = novo;
setInterval(() => { if (comecou && !fim) $('tempo').textContent = fmtTempo((performance.now() - t0)/1000); }, 500);
novo();
"""

# ---------------------------------------------------------------- APAGUE AS LUZES
LUZES_CSS = """
#grade{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;max-width:400px;margin:6px auto;aspect-ratio:1}
.luz{border-radius:14px;background:#1d2440;cursor:pointer;transition:background .18s,box-shadow .18s,transform .1s;
  box-shadow:inset 0 -5px 0 rgba(0,0,0,.35)}
.luz:active{transform:scale(.94)}
.luz.on{background:radial-gradient(circle at 40% 35%,#fff7c2,#ffd60a 45%,#ff9f1c);box-shadow:0 0 18px #ffd60a99,inset 0 -5px 0 rgba(0,0,0,.2)}
.estrelas{font-size:22px;letter-spacing:4px}
"""
LUZES_HTML = """<div class="painel"><div class="barra"><div class="info"><span class="tag">🏁 Nível <b id="niv">1</b></span>
<span class="tag">👆 Cliques <b id="cli">0</b></span><span class="tag">⭐ Meta: até <b id="meta">3</b></span></div>
<span class="tag">🏆 Nível máx. <b id="rec">1</b></span></div>
<div id="grade"></div><div class="msg" id="msg"></div>
<div style="display:flex;gap:8px;justify-content:center"><button id="breset">↩️ Recomeçar nível</button>
<button id="bprox" class="pri" style="display:none">➡️ Próximo nível</button></div></div>"""
LUZES_JS = r"""
let nivel = 1, luzes, inicial, cliques, meta, fim;
function alternar(g, i){ const r = Math.floor(i/5), c = i % 5; [[0, 0], [1, 0], [-1, 0], [0, 1], [0, -1]].forEach(([dr, dc]) => {
  const rr = r + dr, cc = c + dc; if (rr >= 0 && rr < 5 && cc >= 0 && cc < 5) g[rr*5 + cc] = !g[rr*5 + cc]; }); }
function gerar(){ meta = Math.min(3 + nivel, 15); const g = Array(25).fill(false);
  embaralhar([...Array(25).keys()]).slice(0, meta).forEach(i => alternar(g, i));
  if (g.every(x => !x)) return gerar(); inicial = g.slice(); comecar(); }
function comecar(){ luzes = inicial.slice(); cliques = 0; fim = false; $('msg').textContent = ''; $('bprox').style.display = 'none'; desenhar(); }
function desenhar(){ const g = $('grade'); g.innerHTML = '';
  luzes.forEach((on, i) => { const d = document.createElement('div'); d.className = 'luz' + (on ? ' on' : ''); d.onclick = () => clicar(i); g.appendChild(d); });
  $('niv').textContent = nivel; $('cli').textContent = cliques; $('meta').textContent = meta; $('rec').textContent = Math.max(nivel, lerRecorde('rec_luzes')); }
function clicar(i){ if (fim) return; alternar(luzes, i); cliques++; bip(luzes[i] ? 880 : 440, .05, 'sine'); desenhar();
  if (luzes.every(x => !x)) { fim = true; const est = cliques <= meta ? 3 : cliques <= meta*2 ? 2 : 1;
    salvarRecorde('rec_luzes', nivel + 1); acorde([523, 659, 784, 1046]);
    $('msg').innerHTML = '<span class="ok">💡 Tudo apagado em ' + cliques + ' cliques!</span><div class="estrelas">' + '⭐'.repeat(est) + '☆'.repeat(3 - est) + '</div>';
    $('bprox').style.display = 'inline-block'; } }
$('breset').onclick = comecar; $('bprox').onclick = () => { nivel++; gerar(); };
gerar();
"""

RACIOCINIO = {
    "sudoku": (SUDOKU_HTML, SUDOKU_JS, SUDOKU_CSS, 760),
    "senha": (SENHA_HTML, SENHA_JS, SENHA_CSS, 780),
    "hanoi": (HANOI_HTML, HANOI_JS, HANOI_CSS, 480),
    "desliza": (DESLIZA_HTML, DESLIZA_JS, DESLIZA_CSS, 620),
    "luzes": (LUZES_HTML, LUZES_JS, LUZES_CSS, 620),
}


def jogo_raciocinio(nome):
    corpo, js, css, altura = RACIOCINIO[nome]
    jogo_html(pagina_livre(corpo, js, css), altura)


# =====================================================================
# JOGOS DE ALTA TECNOLOGIA (WebGL/Three.js, física, partículas, som sintetizado)
# =====================================================================
THREE_HEAD = r"""<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>window.THREE || document.write('<script src="https://cdn.jsdelivr.net/npm/three@0.128.0/build/three.min.js"><\/script>')</script>"""

CSS_TECH = """
.jogo{position:relative;margin:0 auto;border-radius:16px;overflow:hidden;box-shadow:0 10px 34px rgba(0,0,0,.45)}
.jogo canvas{width:100%;height:auto;display:block;touch-action:none;outline:none}
.hud{position:absolute;z-index:4;top:8px;left:12px;right:52px;display:flex;justify-content:space-between;gap:8px;pointer-events:none;
  font-weight:800;font-size:15px;text-shadow:0 2px 6px #000;color:#fff}
#som{position:absolute;z-index:5;top:6px;right:8px;padding:6px 9px;background:rgba(0,0,0,.45);font-size:16px}
.tela{position:absolute;z-index:6;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
  background:radial-gradient(circle at 50% 40%,rgba(30,20,70,.82),rgba(3,5,15,.92));padding:22px;gap:6px}
.tela h1{margin:0;font-size:32px;color:#ffd34d;text-shadow:0 0 18px rgba(255,211,77,.55),0 0 2px #000}
.tela p{margin:2px 0;opacity:.92;max-width:360px;line-height:1.35}.tela .grande{font-size:22px;font-weight:800;color:#ffd34d}
.tela button{margin-top:12px;font-size:20px;padding:12px 28px;background:linear-gradient(90deg,#4f7cff,#a855f7);box-shadow:0 6px 20px #4f7cff66}
.ctl{display:flex;gap:6px;margin:8px auto 0}.ctl button{flex:1;padding:13px 0;font-size:19px;background:#283044}
.oculto{display:none!important}
"""


def pagina_tech(largura: int, corpo_extra: str, js: str, botoes: str = "", tres_d: bool = False) -> str:
    corpo = (f"<div class='jogo' style='max-width:{largura}px'><canvas id='c' tabindex='0'></canvas>"
             f"<div class='hud' id='hud'></div><button id='som'>🔊</button>{corpo_extra}</div>"
             + (f"<div class='ctl' style='max-width:{largura}px'>{botoes}</div>" if botoes else ""))
    js_base = r"""
$('som').onclick = e => { e.stopPropagation(); mudo = !mudo; $('som').textContent = mudo ? '🔇' : '🔊'; };
function tela(html){ const t = $('tela'); if (!html) { t.classList.add('oculto'); return; } t.innerHTML = html; t.classList.remove('oculto'); }
"""
    return pagina_livre(corpo, js_base + js, CSS_TECH, THREE_HEAD if tres_d else "")


SEM_3D = r"""
if (!window.THREE) { tela('<h1>😕 Sem 3D</h1><p>Não consegui carregar o motor 3D (Three.js). Verifique sua internet e recarregue a página.</p>');
  throw new Error('Three.js indisponível'); }
"""

# ---------------------------------------------------------------- GALÁXIA 3D
GALAXIA_JS = SEM_3D + r"""
const W = 480, H = 640, cv = $('c');
const ren = new THREE.WebGLRenderer({canvas: cv, antialias: true});
ren.setPixelRatio(Math.min(2, devicePixelRatio)); ren.setSize(W, H, false);
const cena = new THREE.Scene(); cena.background = new THREE.Color(0x02030a); cena.fog = new THREE.Fog(0x02030a, 90, 260);
const cam = new THREE.PerspectiveCamera(65, W/H, 0.1, 600); cam.position.set(0, 3, 14); cam.lookAt(0, 0, -30);
cena.add(new THREE.AmbientLight(0x5060a0, 1.1));
const dl = new THREE.DirectionalLight(0xffffff, 1.2); dl.position.set(5, 10, 8); cena.add(dl);
// campo de estrelas e nebulosas
const NE = 2000, pe = new Float32Array(NE*3);
for (let i = 0; i < NE; i++) { pe[i*3] = (Math.random() - .5)*180; pe[i*3+1] = (Math.random() - .5)*120; pe[i*3+2] = -Math.random()*320; }
const gE = new THREE.BufferGeometry(); gE.setAttribute('position', new THREE.BufferAttribute(pe, 3));
cena.add(new THREE.Points(gE, new THREE.PointsMaterial({color: 0xffffff, size: 0.35})));
[[0x6a1b9a, -60, 20], [0x0d47a1, 70, -15], [0xad1457, -20, -35]].forEach(([c, x, y]) => {
  const n = new THREE.Mesh(new THREE.SphereGeometry(40, 16, 12), new THREE.MeshBasicMaterial({color: c, transparent: true, opacity: .12, depthWrite: false}));
  n.position.set(x, y, -300); cena.add(n); });
// nave do jogador
function criarNave(){
  const g = new THREE.Group();
  const corpo = new THREE.Mesh(new THREE.ConeGeometry(0.7, 3, 8), new THREE.MeshStandardMaterial({color: 0xdfe6ff, metalness: .7, roughness: .3, flatShading: true}));
  corpo.rotation.x = -Math.PI/2; g.add(corpo);
  const asa = new THREE.Mesh(new THREE.BoxGeometry(4.2, 0.12, 1.2), new THREE.MeshStandardMaterial({color: 0x4f7cff, metalness: .5, roughness: .4, flatShading: true}));
  asa.position.z = 0.6; g.add(asa);
  [-2.1, 2.1].forEach(x => { const p = new THREE.Mesh(new THREE.BoxGeometry(0.15, 0.5, 1.4), new THREE.MeshStandardMaterial({color: 0xff5ea8, emissive: 0x551133}));
    p.position.set(x, 0.2, 0.6); g.add(p); });
  const cab = new THREE.Mesh(new THREE.SphereGeometry(0.42, 12, 8), new THREE.MeshStandardMaterial({color: 0x7df9ff, emissive: 0x1a6a80, roughness: .1}));
  cab.position.set(0, 0.35, -0.2); g.add(cab);
  const fogo = new THREE.Mesh(new THREE.SphereGeometry(0.45, 10, 8), new THREE.MeshBasicMaterial({color: 0xff9f1c, transparent: true, opacity: .85, blending: THREE.AdditiveBlending}));
  fogo.position.z = 1.7; g.add(fogo); g.userData.fogo = fogo;
  const luz = new THREE.PointLight(0xff9f1c, 1.6, 9); luz.position.z = 2.2; g.add(luz);
  return g;
}
const nave = criarNave(); cena.add(nave);
const escudoMesh = new THREE.Mesh(new THREE.SphereGeometry(2.4, 18, 14), new THREE.MeshBasicMaterial({color: 0x7df9ff, transparent: true, opacity: 0, wireframe: true}));
nave.add(escudoMesh);
// recursos compartilhados
const gLaser = new THREE.BoxGeometry(0.14, 0.14, 2), mLaser = new THREE.MeshBasicMaterial({color: 0x7df9ff});
const gBala = new THREE.SphereGeometry(0.3, 8, 6), mBala = new THREE.MeshBasicMaterial({color: 0xff3355});
let lasers = [], balas = [], inimigos = [], poderes = [], explosoes = [];
let estado = 'inicio', pontos = 0, escudos = 3, onda = 1, tempo = 0, spawnT = 0, tiroT = 0, invul = 0, triplo = 0, tremor = 0;
let alvo = {x: 0, y: 0}, recorde = lerRecorde('rec_galaxia');
const teclas = {};
function criarAsteroide(){
  const r = 0.9 + Math.random()*1.8;
  const m = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 0), new THREE.MeshStandardMaterial({color: new THREE.Color().setHSL(0.07, .25, .25 + Math.random()*.2), flatShading: true, roughness: .9}));
  m.userData = {tipo: 'ast', r, hp: r > 2 ? 2 : 1, vr: new THREE.Vector3(Math.random(), Math.random(), Math.random()).multiplyScalar(2), pts: 50};
  return m;
}
function criarInimigo(){
  const g = new THREE.Group();
  const nucleo = new THREE.Mesh(new THREE.OctahedronGeometry(1.1, 0), new THREE.MeshStandardMaterial({color: 0xff2255, emissive: 0x660011, metalness: .6, roughness: .3, flatShading: true}));
  const anel = new THREE.Mesh(new THREE.TorusGeometry(1.7, 0.12, 8, 24), new THREE.MeshBasicMaterial({color: 0xff9fd0}));
  anel.rotation.x = Math.PI/2; g.add(nucleo, anel);
  g.userData = {tipo: 'ini', r: 1.6, hp: 3, fase: Math.random()*6, tiro: 1 + Math.random()*2, pts: 200};
  return g;
}
function criarPoder(){
  const tipo = Math.random() < .55 ? 'triplo' : 'escudo';
  const m = new THREE.Mesh(new THREE.TorusGeometry(0.9, 0.25, 10, 24), new THREE.MeshBasicMaterial({color: tipo === 'triplo' ? 0x5be08a : 0x4fc3ff}));
  m.userData = {tipo, r: 1.3}; return m;
}
function explodir(p, cor, n = 60, escala = 1){
  const pos = new Float32Array(n*3), vel = [];
  for (let i = 0; i < n; i++) { pos.set([p.x, p.y, p.z], i*3);
    vel.push(new THREE.Vector3(Math.random() - .5, Math.random() - .5, Math.random() - .5).normalize().multiplyScalar((4 + Math.random()*12)*escala)); }
  const g = new THREE.BufferGeometry(); g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const pts = new THREE.Points(g, new THREE.PointsMaterial({color: cor, size: 0.6*escala, transparent: true, blending: THREE.AdditiveBlending, depthWrite: false}));
  const luz = new THREE.PointLight(cor, 4, 25); luz.position.copy(p);
  cena.add(pts, luz); explosoes.push({pts, vel, luz, vida: 0.9});
}
function hud(){ $('hud').innerHTML = '<span>⭐ ' + pontos + '</span><span>🌊 Onda ' + onda + '</span><span>' + '🛡️'.repeat(Math.max(0, escudos)) + '</span>'; }
function remover(lista, o){ cena.remove(o); lista.splice(lista.indexOf(o), 1); }
function comecar(){
  [...lasers, ...balas, ...inimigos, ...poderes].forEach(o => cena.remove(o));
  lasers = []; balas = []; inimigos = []; poderes = [];
  pontos = 0; escudos = 3; onda = 1; tempo = 0; spawnT = 1; invul = 0; triplo = 0; alvo = {x: 0, y: 0};
  nave.position.set(0, 0, 0); nave.visible = true; estado = 'jogando'; tela(null); hud(); audio(); cv.focus();
}
function fimDeJogo(){ estado = 'fim'; nave.visible = false; recorde = salvarRecorde('rec_galaxia', pontos);
  explodir(nave.position, 0xff9f1c, 160, 1.6); ruido(1, .25); vibrar(300);
  setTimeout(() => tela('<h1>💥 Nave destruída</h1><p class="grande">⭐ ' + pontos + ' pontos</p><p>Onda ' + onda + ' · Recorde: ' + recorde + '</p><button id="bj">🚀 Jogar de novo</button>'), 900);
  setTimeout(() => { const b = $('bj'); if (b) b.onclick = comecar; }, 950); }
function atirar(){
  const xs = triplo > 0 ? [-1.6, 0, 1.6] : [0];
  xs.forEach((dx, i) => { const l = new THREE.Mesh(gLaser, mLaser); l.position.set(nave.position.x + dx, nave.position.y, nave.position.z - 1.8);
    l.userData = {vx: triplo > 0 ? (i - 1)*4 : 0}; cena.add(l); lasers.push(l); });
  bip(1200, .07, 'square', .03, -900);
}
function dano(){
  if (invul > 0) return; escudos--; invul = 1.6; tremor = .5; ruido(.35, .2); vibrar(120); hud();
  if (escudos <= 0) fimDeJogo();
}
addEventListener('keydown', e => { teclas[e.code] = true; if (['Space', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault();
  if ((e.code === 'Space' || e.code === 'Enter') && estado !== 'jogando') comecar(); });
addEventListener('keyup', e => teclas[e.code] = false);
let toque = null;
cv.addEventListener('pointerdown', e => { if (estado !== 'jogando') return; cv.setPointerCapture(e.pointerId); toque = {x: e.clientX, y: e.clientY}; });
cv.addEventListener('pointermove', e => { if (!toque) return; const r = cv.getBoundingClientRect(), k = 22/r.width;
  alvo.x = Math.max(-10, Math.min(10, alvo.x + (e.clientX - toque.x)*k*1.3)); alvo.y = Math.max(-5.5, Math.min(6.5, alvo.y - (e.clientY - toque.y)*k*1.3));
  toque = {x: e.clientX, y: e.clientY}; });
['pointerup', 'pointercancel'].forEach(t => cv.addEventListener(t, () => toque = null));
function colide(a, b, ra, rb){ return a.position.distanceTo(b.position) < ra + rb; }
let ult = performance.now();
function loop(t){
  const dt = Math.min(.05, (t - ult)/1000); ult = t; requestAnimationFrame(loop);
  const velMundo = estado === 'jogando' ? 40 + onda*6 : 18;
  // estrelas
  const p = gE.attributes.position.array;
  for (let i = 0; i < NE; i++) { p[i*3+2] += velMundo*1.6*dt; if (p[i*3+2] > 15) p[i*3+2] -= 330; }
  gE.attributes.position.needsUpdate = true;
  nave.userData.fogo.scale.setScalar(0.8 + Math.random()*0.5); nave.userData.fogo.scale.z = 2 + Math.random();
  if (estado === 'jogando') {
    tempo += dt; onda = 1 + Math.floor(tempo/25);
    const v = 15*dt;
    if (teclas.ArrowLeft || teclas.KeyA) alvo.x -= v; if (teclas.ArrowRight || teclas.KeyD) alvo.x += v;
    if (teclas.ArrowUp || teclas.KeyW) alvo.y += v; if (teclas.ArrowDown || teclas.KeyS) alvo.y -= v;
    alvo.x = Math.max(-10, Math.min(10, alvo.x)); alvo.y = Math.max(-5.5, Math.min(6.5, alvo.y));
    const dx = alvo.x - nave.position.x;
    nave.position.x += dx*Math.min(1, dt*10); nave.position.y += (alvo.y - nave.position.y)*Math.min(1, dt*10);
    nave.rotation.z = -dx*0.12; nave.rotation.x = (alvo.y - nave.position.y)*0.05;
    tiroT -= dt; if ((teclas.Space || toque) && tiroT <= 0) { atirar(); tiroT = .17; }
    invul = Math.max(0, invul - dt); triplo = Math.max(0, triplo - dt);
    nave.visible = invul <= 0 || Math.floor(invul*12) % 2 === 0;
    escudoMesh.material.opacity = invul > 0 ? .35 : 0; escudoMesh.rotation.y += dt*2;
    // inimigos e asteroides
    spawnT -= dt;
    if (spawnT <= 0) { spawnT = Math.max(.28, 1.1 - onda*.09) * (0.6 + Math.random()*.6);
      const o = Math.random() < Math.min(.45, .12 + onda*.05) ? criarInimigo() : criarAsteroide();
      o.position.set((Math.random() - .5)*24, (Math.random() - .5)*13 + .5, -240); cena.add(o); inimigos.push(o);
      if (Math.random() < .07) { const pw = criarPoder(); pw.position.set((Math.random() - .5)*18, (Math.random() - .5)*10, -240); cena.add(pw); poderes.push(pw); } }
    for (const o of [...inimigos]) {
      const u = o.userData; o.position.z += velMundo*dt*(u.tipo === 'ini' ? .8 : 1);
      if (u.tipo === 'ast') { o.rotation.x += u.vr.x*dt; o.rotation.y += u.vr.y*dt; }
      else { u.fase += dt*2; o.position.x += Math.sin(u.fase)*dt*6; o.rotation.y += dt*3; u.tiro -= dt;
        if (u.tiro <= 0 && o.position.z > -150 && o.position.z < -20) { u.tiro = 1.6 + Math.random()*1.5;
          const b = new THREE.Mesh(gBala, mBala); b.position.copy(o.position);
          b.userData.v = nave.position.clone().sub(o.position).normalize().multiplyScalar(35 + onda*3); cena.add(b); balas.push(b); bip(300, .1, 'sawtooth', .025, -150); } }
      if (o.position.z > 18) { remover(inimigos, o); continue; }
      if (nave.visible !== false && colide(o, nave, u.r, 1.2)) { explodir(o.position, 0xffaa55, 50); remover(inimigos, o); dano(); continue; }
    }
    for (const b of [...balas]) { b.position.addScaledVector(b.userData.v, dt); if (b.position.z > 20) { remover(balas, b); continue; }
      if (colide(b, nave, .3, 1.1)) { remover(balas, b); dano(); } }
    for (const pw of [...poderes]) { pw.position.z += velMundo*dt; pw.rotation.y += dt*3; pw.rotation.x += dt*1.3;
      if (pw.position.z > 18) { remover(poderes, pw); continue; }
      if (colide(pw, nave, pw.userData.r, 1.4)) { if (pw.userData.tipo === 'triplo') triplo = 9; else escudos = Math.min(5, escudos + 1);
        acorde([660, 880, 1320], .08); remover(poderes, pw); hud(); } }
    for (const l of [...lasers]) { l.position.z -= 130*dt; l.position.x += l.userData.vx*dt;
      if (l.position.z < -230) { remover(lasers, l); continue; }
      for (const o of inimigos) if (colide(l, o, .3, o.userData.r)) { remover(lasers, l); o.userData.hp--;
        if (o.userData.hp <= 0) { pontos += o.userData.pts*onda; explodir(o.position, o.userData.tipo === 'ini' ? 0xff3366 : 0xffbb66, o.userData.tipo === 'ini' ? 90 : 55);
          remover(inimigos, o); ruido(.25, .12); hud(); }
        else bip(220, .04, 'square', .03);
        break; }
    }
  } else { nave.rotation.y += dt*.6; nave.position.y = Math.sin(t/600)*.5; }
  for (const ex of [...explosoes]) { ex.vida -= dt; const a = ex.pts.geometry.attributes.position.array;
    ex.vel.forEach((v, i) => { a[i*3] += v.x*dt; a[i*3+1] += v.y*dt; a[i*3+2] += v.z*dt + velMundo*dt*.5; });
    ex.pts.geometry.attributes.position.needsUpdate = true; ex.pts.material.opacity = Math.max(0, ex.vida/0.9); ex.luz.intensity = Math.max(0, ex.vida*5);
    if (ex.vida <= 0) { cena.remove(ex.pts, ex.luz); ex.pts.geometry.dispose(); explosoes.splice(explosoes.indexOf(ex), 1); } }
  tremor = Math.max(0, tremor - dt);
  cam.position.x = nave.position.x*.35 + (Math.random() - .5)*tremor*1.5; cam.position.y = 3 + nave.position.y*.3 + (Math.random() - .5)*tremor*1.5;
  cam.lookAt(nave.position.x*.5, nave.position.y*.4, -30);
  ren.render(cena, cam);
}
tela('<h1>🌌 Galáxia 3D</h1><p>Pilote sua nave, destrua asteroides e naves inimigas e sobreviva às ondas!</p>' +
     '<p>⌨️ Setas/WASD movem · ESPAÇO atira</p><p>📱 Arraste o dedo na tela (atira sozinho)</p>' +
     '<p>💚 anel verde = tiro triplo · 💙 anel azul = +1 escudo</p><p>🏆 Recorde: ' + recorde + '</p><button id="bj">🚀 Decolar</button>');
$('bj').onclick = comecar; hud(); requestAnimationFrame(loop);
"""

# ---------------------------------------------------------------- CORRIDA INFINITA 3D
RUNNER_JS = SEM_3D + r"""
const W = 480, H = 640, cv = $('c');
const ren = new THREE.WebGLRenderer({canvas: cv, antialias: true});
ren.setPixelRatio(Math.min(2, devicePixelRatio)); ren.setSize(W, H, false);
const cena = new THREE.Scene(); const ceu = new THREE.Color(0x12052b); cena.background = ceu; cena.fog = new THREE.Fog(ceu, 30, 130);
const cam = new THREE.PerspectiveCamera(70, W/H, 0.1, 300); cam.position.set(0, 4.2, 8); cam.lookAt(0, 1.2, -12);
cena.add(new THREE.HemisphereLight(0xb388ff, 0x220044, 1.0));
const dl = new THREE.DirectionalLight(0xffffff, .8); dl.position.set(3, 10, 5); cena.add(dl);
// sol neon de fundo
const sol = new THREE.Mesh(new THREE.CircleGeometry(30, 40), new THREE.MeshBasicMaterial({color: 0xff2e88, fog: false}));
sol.position.set(0, 18, -200); cena.add(sol);
// pista e grade
const pista = new THREE.Mesh(new THREE.PlaneGeometry(9, 400), new THREE.MeshStandardMaterial({color: 0x150a30, roughness: .6, metalness: .3}));
pista.rotation.x = -Math.PI/2; pista.position.z = -150; cena.add(pista);
const grade = new THREE.GridHelper(400, 200, 0xff00ff, 0x5a1aa0); grade.position.y = 0.01; cena.add(grade);
[-1.25, 1.25].forEach(x => { const l = new THREE.Mesh(new THREE.BoxGeometry(.08, .02, 400), new THREE.MeshBasicMaterial({color: 0x7df9ff}));
  l.position.set(x*2, .03, -150); cena.add(l); });
// prédios neon (reaproveitados)
const predios = [];
for (let i = 0; i < 46; i++) { const h = 4 + Math.random()*22, w = 3 + Math.random()*5;
  const gb = new THREE.BoxGeometry(w, h, w), m = new THREE.Mesh(gb, new THREE.MeshStandardMaterial({color: 0x0d0620, roughness: .8}));
  const cor = [0x7df9ff, 0xff2e88, 0xffd34d, 0xa855f7][i % 4];
  m.add(new THREE.LineSegments(new THREE.EdgesGeometry(gb), new THREE.LineBasicMaterial({color: cor})));
  const lado = i % 2 ? 1 : -1; m.position.set(lado*(8 + Math.random()*16), h/2, -i*5.5); cena.add(m); predios.push(m); }
// jogador (robô)
const jog = new THREE.Group(), corpo = new THREE.Group(); jog.add(corpo);
const mCorpo = new THREE.MeshStandardMaterial({color: 0xe8f7ff, metalness: .6, roughness: .25});
const tronco = new THREE.Mesh(new THREE.BoxGeometry(.8, .9, .5), mCorpo); tronco.position.y = 1.05; corpo.add(tronco);
const cabeca = new THREE.Mesh(new THREE.SphereGeometry(.36, 16, 12), mCorpo); cabeca.position.y = 1.75; corpo.add(cabeca);
const visor = new THREE.Mesh(new THREE.BoxGeometry(.5, .14, .1), new THREE.MeshBasicMaterial({color: 0x00ffe1})); visor.position.set(0, 1.78, -.32); corpo.add(visor);
const pernas = [-.22, .22].map(x => { const p = new THREE.Mesh(new THREE.BoxGeometry(.22, .6, .25), new THREE.MeshStandardMaterial({color: 0x4f7cff, metalness: .5}));
  p.position.set(x, .3, 0); corpo.add(p); return p; });
const bracos = [-.52, .52].map(x => { const b = new THREE.Mesh(new THREE.BoxGeometry(.18, .7, .2), new THREE.MeshStandardMaterial({color: 0x4f7cff, metalness: .5}));
  b.position.set(x, 1.05, 0); corpo.add(b); return b; });
const brilho = new THREE.PointLight(0x00ffe1, 1.5, 6); brilho.position.set(0, 1.5, -.5); jog.add(brilho);
cena.add(jog);
// obstáculos e moedas
const TIPOS = {
  baixo: {g: new THREE.BoxGeometry(2, .9, .5), cor: 0xff2e55, y: .45},
  alto: {g: new THREE.BoxGeometry(2.2, .45, .5), cor: 0xffa21f, y: 1.75},
  muro: {g: new THREE.BoxGeometry(2, 3.2, 1.2), cor: 0xa855f7, y: 1.6},
};
const gMoeda = new THREE.TorusGeometry(.32, .11, 8, 18), mMoeda = new THREE.MeshStandardMaterial({color: 0xffd34d, emissive: 0x7a5a00, metalness: .9, roughness: .2});
let obst = [], moedas = [], part = [], estado = 'inicio', faixa = 0, xAlvo = 0, y = 0, vy = 0, agach = 0, vel = 18, dist = 0, ouro = 0, proxSpawn = 30, tremor = 0;
let recorde = lerRecorde('rec_runner');
function criarObst(tipo, lane, z){ const t = TIPOS[tipo];
  const m = new THREE.Mesh(t.g, new THREE.MeshStandardMaterial({color: t.cor, emissive: t.cor, emissiveIntensity: .45, metalness: .3, roughness: .4}));
  m.position.set(lane*2.5, t.y, z); m.userData = {tipo}; cena.add(m); obst.push(m);
  if (tipo === 'alto') [-1.05, 1.05].forEach(dx => { const p = new THREE.Mesh(new THREE.BoxGeometry(.12, 1.95, .12), new THREE.MeshStandardMaterial({color: 0x555577}));
    p.position.set(dx, -.98, 0); m.add(p); }); }
function gerarTrecho(z){
  const r = Math.random(), lanes = embaralhar([-1, 0, 1]);
  if (r < .35) criarObst(['baixo', 'alto'][Math.floor(Math.random()*2)], lanes[0], z);
  else if (r < .65) { criarObst('muro', lanes[0], z); criarObst(Math.random() < .5 ? 'muro' : 'baixo', lanes[1], z); }
  else if (r < .85) { criarObst('baixo', -1, z); criarObst('baixo', 0, z); criarObst('baixo', 1, z); }
  else { criarObst('alto', -1, z); criarObst('alto', 0, z); criarObst('alto', 1, z); }
  const livre = lanes[2]; for (let k = 0; k < 5; k++) { const m = new THREE.Mesh(gMoeda, mMoeda); m.position.set(livre*2.5, 1, z + 4 + k*2.2); cena.add(m); moedas.push(m); }
}
function hud(){ $('hud').innerHTML = '<span>🏃 ' + Math.floor(dist) + ' m</span><span>🪙 ' + ouro + '</span><span>⚡ ' + Math.round(vel*3.6) + ' km/h</span>'; }
function comecar(){ [...obst, ...moedas].forEach(o => cena.remove(o)); obst = []; moedas = [];
  faixa = 0; xAlvo = 0; y = 0; vy = 0; agach = 0; vel = 18; dist = 0; ouro = 0; proxSpawn = 30; jog.position.set(0, 0, 0); jog.visible = true;
  for (let z = -40; z > -140; z -= 22) gerarTrecho(z);
  estado = 'jogando'; tela(null); audio(); cv.focus(); hud(); }
function acao(a){ if (estado !== 'jogando') { if (a === 'inicio') comecar(); return; }
  if (a === 'esq' && faixa > -1) { faixa--; bip(500, .05, 'sine'); }
  if (a === 'dir' && faixa < 1) { faixa++; bip(500, .05, 'sine'); }
  if (a === 'pula' && y <= .001) { vy = 10.5; agach = 0; bip(400, .15, 'square', .04, 500); }
  if (a === 'abaixa') { agach = .75; if (y > 0) vy = -16; bip(250, .12, 'triangle', .05, -100); } }
addEventListener('keydown', e => { const m = {ArrowLeft: 'esq', KeyA: 'esq', ArrowRight: 'dir', KeyD: 'dir', ArrowUp: 'pula', KeyW: 'pula', Space: 'pula', ArrowDown: 'abaixa', KeyS: 'abaixa', Enter: 'inicio'}[e.code];
  if (m) { e.preventDefault(); if (e.repeat) return; acao(estado === 'jogando' ? m : 'inicio'); } });
let ini = null;
cv.addEventListener('pointerdown', e => { ini = {x: e.clientX, y: e.clientY}; if (estado !== 'jogando') return; });
cv.addEventListener('pointerup', e => { if (!ini) return; const dx = e.clientX - ini.x, dy = e.clientY - ini.y; ini = null;
  if (estado !== 'jogando') return; if (Math.hypot(dx, dy) < 20) { acao('pula'); return; }
  acao(Math.abs(dx) > Math.abs(dy) ? (dx > 0 ? 'dir' : 'esq') : (dy > 0 ? 'abaixa' : 'pula')); });
document.querySelectorAll('[data-a]').forEach(b => b.addEventListener('pointerdown', e => { e.preventDefault(); acao(estado === 'jogando' ? b.dataset.a : 'inicio'); }));
function batida(){ estado = 'fim'; tremor = .6; ruido(.8, .25); vibrar(300);
  for (let i = 0; i < 40; i++) { const m = new THREE.Mesh(new THREE.BoxGeometry(.18, .18, .18), new THREE.MeshBasicMaterial({color: i % 2 ? 0x00ffe1 : 0xffffff}));
    m.position.copy(jog.position).add(new THREE.Vector3(0, 1, 0)); m.userData.v = new THREE.Vector3((Math.random() - .5)*10, Math.random()*10, (Math.random() - .5)*10); cena.add(m); part.push(m); }
  jog.visible = false; recorde = salvarRecorde('rec_runner', Math.floor(dist));
  setTimeout(() => { tela('<h1>💥 Bateu!</h1><p class="grande">🏃 ' + Math.floor(dist) + ' m · 🪙 ' + ouro + '</p><p>🏆 Recorde: ' + recorde + ' m</p><button id="bj">🔁 Correr de novo</button>');
    $('bj').onclick = comecar; }, 800); }
let ult = performance.now(), tempoAnim = 0;
function loop(t){ const dt = Math.min(.04, (t - ult)/1000); ult = t; requestAnimationFrame(loop); tempoAnim += dt;
  const v = estado === 'jogando' ? vel : 6;
  grade.position.z = (grade.position.z + v*dt) % 2;
  for (const p of predios) { p.position.z += v*dt*.9; if (p.position.z > 15) p.position.z -= 253; }
  if (estado === 'jogando') {
    vel = Math.min(46, vel + dt*.38); dist += vel*dt; hud();
    xAlvo = faixa*2.5; jog.position.x += (xAlvo - jog.position.x)*Math.min(1, dt*14);
    vy -= 30*dt; y = Math.max(0, y + vy*dt); if (y === 0) vy = 0; jog.position.y = y;
    agach = Math.max(0, agach - dt); corpo.scale.y = agach > 0 ? .5 : 1;
    const passo = Math.sin(tempoAnim*vel*.7); pernas[0].rotation.x = passo*.8; pernas[1].rotation.x = -passo*.8;
    bracos[0].rotation.x = -passo*.7; bracos[1].rotation.x = passo*.7; corpo.rotation.z = (xAlvo - jog.position.x)*-.08;
    proxSpawn -= vel*dt; if (proxSpawn <= 0) { gerarTrecho(-130); proxSpawn = Math.max(11, 22 - vel*.2) + Math.random()*6; }
    for (const o of [...obst]) { o.position.z += vel*dt;
      if (o.position.z > 12) { cena.remove(o); obst.splice(obst.indexOf(o), 1); continue; }
      const prof = o.userData.tipo === 'muro' ? .9 : .5;
      if (Math.abs(o.position.z) < prof && Math.abs(o.position.x - jog.position.x) < 1.15) {
        const tp = o.userData.tipo, topo = y + (agach > 0 ? .95 : 2.05);
        if ((tp === 'baixo' && y < .85) || (tp === 'alto' && topo > 1.5) || tp === 'muro') { batida(); break; } } }
    for (const m of [...moedas]) { m.position.z += vel*dt; m.rotation.y += dt*5;
      if (m.position.z > 10) { cena.remove(m); moedas.splice(moedas.indexOf(m), 1); continue; }
      if (Math.abs(m.position.z) < .7 && Math.abs(m.position.x - jog.position.x) < 1 && Math.abs(m.position.y - (y + 1)) < 1.2) {
        ouro++; bip(1300 + (ouro % 5)*120, .06, 'triangle', .05); cena.remove(m); moedas.splice(moedas.indexOf(m), 1); } }
  } else if (estado === 'inicio') { jog.rotation.y += dt*.8; }
  for (const p of [...part]) { p.userData.v.y -= 20*dt; p.position.addScaledVector(p.userData.v, dt); p.rotation.x += dt*5;
    if (p.position.y < -2) { cena.remove(p); part.splice(part.indexOf(p), 1); } }
  tremor = Math.max(0, tremor - dt);
  cam.position.x += ((jog.position.x*.6) - cam.position.x)*Math.min(1, dt*5) + (Math.random() - .5)*tremor;
  cam.position.y = 4.2 + jog.position.y*.35 + (Math.random() - .5)*tremor; cam.lookAt(jog.position.x*.5, 1.2, -12);
  ren.render(cena, cam);
}
tela('<h1>🏙️ Corrida Infinita 3D</h1><p>Corra pela cidade neon o mais longe que conseguir!</p>' +
     '<p>⬅️➡️ muda de pista · ⬆️/ESPAÇO pula 🟥 · ⬇️ desliza sob 🟧 · 🟪 só desviando</p>' +
     '<p>📱 Deslize o dedo para os lados, para cima ou para baixo</p><p>🏆 Recorde: ' + recorde + ' m</p><button id="bj">▶️ Correr</button>');
$('bj').onclick = comecar; hud(); requestAnimationFrame(loop);
"""

# ---------------------------------------------------------------- LABIRINTO 3D
LABIRINTO_JS = SEM_3D + r"""
const W = 480, H = 600, cv = $('c');
const ren = new THREE.WebGLRenderer({canvas: cv, antialias: true});
ren.setPixelRatio(Math.min(2, devicePixelRatio)); ren.setSize(W, H, false);
ren.shadowMap.enabled = true; ren.shadowMap.type = THREE.PCFSoftShadowMap;
const cena = new THREE.Scene(); cena.background = new THREE.Color(0x0b1020);
const cam = new THREE.PerspectiveCamera(55, W/H, 0.1, 200);
cena.add(new THREE.HemisphereLight(0xbfd4ff, 0x202040, .7));
const sol = new THREE.DirectionalLight(0xffffff, 1.1); sol.castShadow = true; sol.shadow.mapSize.set(1024, 1024); cena.add(sol, sol.target);
const tabuleiro = new THREE.Group(); cena.add(tabuleiro);
let luzBola, nivel = 1, N, G, gradeMuros, bola, meta, luzMeta, pos, vel, tilt = {x: 0, z: 0}, tiltAlvo = {x: 0, z: 0}, estado = 'inicio', t0 = 0, giro = false, base = null;
let recorde = lerRecorde('rec_labirinto');
function gerarLabirinto(n){ const g = Array.from({length: 2*n + 1}, () => Array(2*n + 1).fill(1)); const pilha = [[0, 0]], vis = new Set(['0,0']); g[1][1] = 0;
  while (pilha.length) { const [x, z] = pilha[pilha.length - 1];
    const viz = [[1, 0], [-1, 0], [0, 1], [0, -1]].map(([dx, dz]) => [x + dx, z + dz, dx, dz]).filter(([a, b]) => a >= 0 && b >= 0 && a < n && b < n && !vis.has(a + ',' + b));
    if (!viz.length) { pilha.pop(); continue; }
    const [a, b, dx, dz] = viz[Math.floor(Math.random()*viz.length)]; vis.add(a + ',' + b);
    g[2*z + 1 + dz][2*x + 1 + dx] = 0; g[2*b + 1][2*a + 1] = 0; pilha.push([a, b]); }
  return g; }
function montarNivel(){
  while (tabuleiro.children.length) tabuleiro.remove(tabuleiro.children[0]);
  N = Math.min(5 + nivel, 15); G = gerarLabirinto(N); const S = G.length, off = (S - 1)/2;
  const chao = new THREE.Mesh(new THREE.BoxGeometry(S, .4, S), new THREE.MeshStandardMaterial({color: 0x1b2340, roughness: .85}));
  chao.position.set(0, -.2, 0); chao.receiveShadow = true; tabuleiro.add(chao);
  const qtd = G.flat().filter(v => v).length;
  gradeMuros = new THREE.InstancedMesh(new THREE.BoxGeometry(1, .9, 1), new THREE.MeshStandardMaterial({color: 0x5b8cff, roughness: .5, metalness: .2}), qtd);
  gradeMuros.castShadow = true; gradeMuros.receiveShadow = true;
  const mtx = new THREE.Matrix4(), cor = new THREE.Color(); let k = 0;
  for (let z = 0; z < S; z++) for (let x = 0; x < S; x++) if (G[z][x]) { mtx.setPosition(x - off, .45, z - off); gradeMuros.setMatrixAt(k, mtx);
    gradeMuros.setColorAt(k, cor.setHSL(.6 + (x + z)/(S*10), .55, .36 + ((x*7 + z*3) % 5)*.03)); k++; }
  tabuleiro.add(gradeMuros);
  meta = new THREE.Group(); const anel = new THREE.Mesh(new THREE.TorusGeometry(.32, .07, 10, 28), new THREE.MeshBasicMaterial({color: 0x5be08a}));
  anel.rotation.x = Math.PI/2; const nucleo = new THREE.Mesh(new THREE.CylinderGeometry(.22, .22, .05, 24), new THREE.MeshBasicMaterial({color: 0x0b3d1f}));
  meta.add(anel, nucleo); meta.position.set(S - 2 - off, .03, S - 2 - off); tabuleiro.add(meta);
  luzMeta = new THREE.PointLight(0x5be08a, 2, 4); luzMeta.position.set(S - 2 - off, .8, S - 2 - off); tabuleiro.add(luzMeta);
  bola = new THREE.Mesh(new THREE.SphereGeometry(.3, 28, 20), new THREE.MeshStandardMaterial({color: 0xffffff, emissive: 0x332200, metalness: .35, roughness: .18}));
  bola.castShadow = true; tabuleiro.add(bola);
  luzBola = new THREE.PointLight(0xffe7a0, 1.4, 3.5); bola.add(luzBola); luzBola.position.y = .6;
  pos = {x: 1, z: 1}; vel = {x: 0, z: 0};
  sol.position.set(S*.3, S*1.2, S*.5); sol.target.position.set(0, 0, 0);
  const sc = sol.shadow.camera; sc.left = sc.bottom = -S*.7; sc.right = sc.top = S*.7; sc.far = S*4; sc.updateProjectionMatrix();
  t0 = performance.now(); hud();
}
function muro(x, z){ const gx = Math.round(x), gz = Math.round(z); return gz < 0 || gx < 0 || gz >= G.length || gx >= G.length || G[gz][gx] === 1; }
function fisica(dt){
  const R = .3, ACC = 16;
  vel.x += tilt.x*ACC*dt; vel.z += tilt.z*ACC*dt; const atrito = Math.pow(.35, dt); vel.x *= atrito; vel.z *= atrito;
  const sub = 4; for (let s = 0; s < sub; s++) { pos.x += vel.x*dt/sub; pos.z += vel.z*dt/sub;
    const cx = Math.round(pos.x), cz = Math.round(pos.z);
    for (let dz = -1; dz <= 1; dz++) for (let dx = -1; dx <= 1; dx++) { const gx = cx + dx, gz = cz + dz; if (!muro(gx, gz)) continue;
      const px = Math.max(gx - .5, Math.min(pos.x, gx + .5)), pz = Math.max(gz - .5, Math.min(pos.z, gz + .5));
      let nx = pos.x - px, nz = pos.z - pz; const d = Math.hypot(nx, nz);
      if (d < R && d > 1e-6) { nx /= d; nz /= d; pos.x = px + nx*R; pos.z = pz + nz*R; const vn = vel.x*nx + vel.z*nz;
        if (vn < 0) { vel.x -= 1.35*vn*nx; vel.z -= 1.35*vn*nz; if (vn < -2.5) bip(180 + Math.random()*60, .05, 'triangle', Math.min(.08, -vn*.012)); } } } }
}
function hud(){ const tt = estado === 'jogando' ? (performance.now() - t0)/1000 : 0;
  $('hud').innerHTML = '<span>🧩 Nível ' + nivel + '</span><span>⏱️ ' + fmtTempo(tt) + '</span><span>🏆 ' + Math.max(recorde, 1) + '</span>'; }
function comecar(){ tela(null); estado = 'jogando'; montarNivel(); audio(); cv.focus(); }
addEventListener('keydown', e => { if (e.code.startsWith('Arrow') || e.code === 'Space') e.preventDefault();
  if ((e.code === 'Space' || e.code === 'Enter') && estado !== 'jogando') { const b = $('bj'); if (b) b.click(); } });
const teclas = {}; addEventListener('keydown', e => teclas[e.code] = true); addEventListener('keyup', e => teclas[e.code] = false);
let ancora = null;
cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); ancora = {x: e.clientX, y: e.clientY}; });
cv.addEventListener('pointermove', e => { if (!ancora || giro) return; tiltAlvo.x = Math.max(-1, Math.min(1, (e.clientX - ancora.x)/60));
  tiltAlvo.z = Math.max(-1, Math.min(1, (e.clientY - ancora.y)/60)); });
['pointerup', 'pointercancel'].forEach(t => cv.addEventListener(t, () => { ancora = null; if (!giro) tiltAlvo = {x: 0, z: 0}; }));
function ligarGiro(){
  const ok = () => { giro = true; base = null; let recebeu = false;
    addEventListener('deviceorientation', e => { if (e.beta == null) return; recebeu = true; if (base === null) base = e.beta;
      tiltAlvo.x = Math.max(-1, Math.min(1, (e.gamma || 0)/22)); tiltAlvo.z = Math.max(-1, Math.min(1, (e.beta - base)/22)); });
    $('bgiro').textContent = '📱 Giroscópio ligado';
    setTimeout(() => { if (!recebeu) { giro = false; $('bgiro').textContent = '📱 Giroscópio indisponível aqui (use o dedo)'; } }, 1500); };
  if (window.DeviceOrientationEvent && typeof DeviceOrientationEvent.requestPermission === 'function')
    DeviceOrientationEvent.requestPermission().then(r => r === 'granted' ? ok() : ($('bgiro').textContent = '📱 Permissão negada')).catch(() => $('bgiro').textContent = '📱 Indisponível');
  else ok(); }
$('bgiro').onclick = ligarGiro;
let ult = performance.now();
function loop(t){ const dt = Math.min(.035, (t - ult)/1000); ult = t; requestAnimationFrame(loop);
  if (estado === 'jogando') {
    if (!giro && !ancora) { tiltAlvo.x = (teclas.ArrowRight || teclas.KeyD ? 1 : 0) - (teclas.ArrowLeft || teclas.KeyA ? 1 : 0);
      tiltAlvo.z = (teclas.ArrowDown || teclas.KeyS ? 1 : 0) - (teclas.ArrowUp || teclas.KeyW ? 1 : 0); }
    tilt.x += (tiltAlvo.x - tilt.x)*Math.min(1, dt*8); tilt.z += (tiltAlvo.z - tilt.z)*Math.min(1, dt*8);
    fisica(dt);
    const S = G.length, off = (S - 1)/2;
    bola.position.set(pos.x - off, .3, pos.z - off); bola.rotation.z -= vel.x*dt/.3; bola.rotation.x += vel.z*dt/.3;
    tabuleiro.rotation.z = -tilt.x*.12; tabuleiro.rotation.x = tilt.z*.12;
    meta.rotation.z += dt*2; meta.children[0].scale.setScalar(1 + Math.sin(t/200)*.12); luzMeta.intensity = 1.6 + Math.sin(t/180)*.6;
    const alvoCam = new THREE.Vector3(bola.position.x*.7, 6 + S*.55, bola.position.z*.7 + 3 + S*.32);
    cam.position.lerp(alvoCam, Math.min(1, dt*3)); cam.lookAt(bola.position.x*.7, 0, bola.position.z*.7);
    hud();
    if (Math.hypot(pos.x - (S - 2), pos.z - (S - 2)) < .45) { estado = 'venceu'; const tt = (performance.now() - t0)/1000;
      const par = N*N*.35, est = tt < par ? 3 : tt < par*2 ? 2 : 1; recorde = salvarRecorde('rec_labirinto', nivel + 1); acorde([523, 659, 784, 1046, 1318]); vibrar(150);
      tela('<h1>🎉 Nível ' + nivel + ' completo!</h1><p class="grande">' + '⭐'.repeat(est) + '☆'.repeat(3 - est) + '</p><p>⏱️ ' + fmtTempo(tt) + '</p><button id="bj">➡️ Próximo labirinto</button>');
      $('bj').onclick = () => { nivel++; comecar(); }; }
  } else { tabuleiro.rotation.y += dt*.15; if (!G) { cam.position.set(0, 14, 12); cam.lookAt(0, 0, 0); } }
  ren.render(cena, cam);
}
montarNivel(); estado = 'inicio'; cam.position.set(0, 12, 12); cam.lookAt(0, 0, 0);
tela('<h1>🧩 Labirinto 3D</h1><p>Incline o tabuleiro e leve a bola de metal até o círculo verde! Cada nível fica maior.</p>' +
     '<p>⌨️ Setas/WASD inclinam · 📱 arraste o dedo ou use o giroscópio</p><p>🏆 Chegou até o nível ' + Math.max(1, recorde) + '</p><button id="bj">▶️ Jogar</button>');
$('bj').onclick = comecar; requestAnimationFrame(loop);
"""

# ---------------------------------------------------------------- QUEBRA-BLOCOS NEON
BLOCOS_NEON_JS = r"""
const W = 480, H = 640, cv = $('c'), ctx = cv.getContext('2d'); cv.width = W; cv.height = H;
const COLS = 10, BW = 44, BH = 18, BX = 11, BY = 70;
const PODERES = {M: ['#5be08a', 'Multibola'], L: ['#4fc3ff', 'Raquete larga'], T: ['#ff5ea8', 'Laser'], S: ['#ffd34d', 'Câmera lenta'], V: ['#ff4d4d', '+1 vida']};
let estado = 'inicio', nivel = 1, pontos = 0, vidas = 3, tijolos, bolas, raq, caps, lasers, part, tremor = 0, combo = 0, efeitos, avisoT = 0, aviso = '';
let recorde = lerRecorde('rec_quebra'), teclas = {};
function velBase(){ return Math.min(600, 330 + nivel*25); }
function gerarNivel(){ tijolos = []; const linhas = Math.min(4 + nivel, 10), padrao = (nivel - 1) % 4;
  for (let r = 0; r < linhas; r++) for (let c = 0; c < COLS; c++) {
    let tem = padrao === 0 || (padrao === 1 && Math.abs(c - 4.5) <= linhas - r) || (padrao === 2 && (r + c) % 2 === 0) || (padrao === 3 && Math.random() < .72);
    if (!tem) continue; let hp = 1 + (r < Math.floor(nivel/2) ? 1 : 0) + (nivel > 5 && r < 2 ? 1 : 0), tipo = 'n';
    if (nivel >= 3 && Math.random() < .07) { tipo = 'metal'; hp = 4; } else if (nivel >= 2 && Math.random() < .06) tipo = 'bomba';
    tijolos.push({x: BX + c*(BW + 2), y: BY + r*(BH + 2), c, r, hp, max: hp, tipo, hue: (r*28 + nivel*40) % 360}); } }
function novaBola(presa){ return {x: raq.x, y: raq.y - 12, vx: 0, vy: 0, r: 7, presa}; }
function reiniciarBola(){ bolas = [novaBola(true)]; caps = []; lasers = []; efeitos = {L: 0, T: 0, S: 0}; raq.w = 90; }
function comecar(){ nivel = 1; pontos = 0; vidas = 3; raq = {x: W/2, y: 604, w: 90, h: 12}; part = []; gerarNivel(); reiniciarBola(); estado = 'jogando'; tela(null); audio(); cv.focus(); }
function lancar(){ for (const b of bolas) if (b.presa) { const a = (-90 + (Math.random()*30 - 15))*Math.PI/180; b.vx = Math.cos(a)*velBase(); b.vy = Math.sin(a)*velBase(); b.presa = false; bip(600, .06, 'square', .04); } }
function faisca(x, y, cor, n = 14){ for (let i = 0; i < n; i++) { const a = Math.random()*6.28, s = 60 + Math.random()*260; part.push({x, y, vx: Math.cos(a)*s, vy: Math.sin(a)*s - 60, t: .5 + Math.random()*.5, cor}); } }
function corTijolo(t){ return t.tipo === 'metal' ? '#9aa6b8' : t.tipo === 'bomba' ? '#ff7a1a' : 'hsl(' + t.hue + ',85%,' + (45 + 12*(t.hp - 1)) + '%)'; }
function quebrar(t, porBomba){
  t.hp--; if (t.hp > 0 && !porBomba) { bip(t.tipo === 'metal' ? 1500 : 700, .04, 'square', .035); return; }
  if (porBomba) t.hp = 0;
  tijolos.splice(tijolos.indexOf(t), 1); combo++; pontos += 10*t.max*Math.min(combo, 10); faisca(t.x + BW/2, t.y + BH/2, corTijolo(t));
  bip(500 + Math.min(combo, 12)*70, .06, 'triangle', .05);
  if (Math.random() < .14) { const k = Object.keys(PODERES)[Math.floor(Math.random()*5)]; caps.push({x: t.x + BW/2, y: t.y + BH/2, k}); }
  if (t.tipo === 'bomba') { tremor = .3; ruido(.35, .18); for (const o of [...tijolos]) if (Math.abs(o.c - t.c) <= 1 && Math.abs(o.r - t.r) <= 1 && tijolos.includes(o)) quebrar(o, true); }
}
function colideRet(b, x, y, w, h){ const px = Math.max(x, Math.min(b.x, x + w)), py = Math.max(y, Math.min(b.y, y + h));
  const dx = b.x - px, dy = b.y - py, d2 = dx*dx + dy*dy; if (d2 > b.r*b.r) return null; const d = Math.sqrt(d2) || .001;
  return d2 === 0 ? {nx: 0, ny: b.vy > 0 ? -1 : 1, p: b.r} : {nx: dx/d, ny: dy/d, p: b.r - d}; }
function atualizar(dt){
  for (const p of part) { p.x += p.vx*dt; p.y += p.vy*dt; p.vy += 500*dt; p.t -= dt; } part = part.filter(p => p.t > 0);
  tremor = Math.max(0, tremor - dt); avisoT -= dt;
  if (estado !== 'jogando') return;
  for (const k in efeitos) efeitos[k] = Math.max(0, efeitos[k] - dt);
  raq.w += ((efeitos.L > 0 ? 140 : 90) - raq.w)*Math.min(1, dt*8);
  if (teclas.ArrowLeft || teclas.KeyA) raq.x -= 620*dt; if (teclas.ArrowRight || teclas.KeyD) raq.x += 620*dt;
  raq.x = Math.max(raq.w/2, Math.min(W - raq.w/2, raq.x));
  const fator = efeitos.S > 0 ? .6 : 1, sub = 5;
  for (const b of bolas) {
    if (b.presa) { b.x = raq.x; b.y = raq.y - 12; continue; }
    for (let s = 0; s < sub; s++) {
      b.x += b.vx*fator*dt/sub; b.y += b.vy*fator*dt/sub;
      if (b.x < b.r) { b.x = b.r; b.vx = Math.abs(b.vx); bip(300, .02, 'sine', .02); } if (b.x > W - b.r) { b.x = W - b.r; b.vx = -Math.abs(b.vx); bip(300, .02, 'sine', .02); }
      if (b.y < b.r + 40) { b.y = b.r + 40; b.vy = Math.abs(b.vy); }
      if (b.vy > 0 && b.y + b.r >= raq.y && b.y - b.r <= raq.y + raq.h && Math.abs(b.x - raq.x) <= raq.w/2 + b.r) {
        const off = (b.x - raq.x)/(raq.w/2), a = (-90 + off*62)*Math.PI/180, v = Math.min(velBase()*1.25, Math.hypot(b.vx, b.vy)*1.01);
        b.vx = Math.cos(a)*v; b.vy = Math.sin(a)*v; b.y = raq.y - b.r; combo = 0; bip(260, .05, 'square', .04); }
      for (const t of tijolos) { const c = colideRet(b, t.x, t.y, BW, BH); if (!c) continue;
        b.x += c.nx*c.p; b.y += c.ny*c.p; const vn = b.vx*c.nx + b.vy*c.ny; if (vn < 0) { b.vx -= 2*vn*c.nx; b.vy -= 2*vn*c.ny; }
        quebrar(t); break; }
    }
  }
  bolas = bolas.filter(b => b.y < H + 20);
  if (!bolas.length) { vidas--; ruido(.5, .2); vibrar(200); tremor = .35;
    if (vidas <= 0) { estado = 'fim'; recorde = salvarRecorde('rec_quebra', pontos);
      tela('<h1>💥 Fim de jogo</h1><p class="grande">⭐ ' + pontos + '</p><p>Nível ' + nivel + ' · Recorde: ' + recorde + '</p><button id="bj">🔁 Jogar de novo</button>'); $('bj').onclick = comecar; return; }
    reiniciarBola(); }
  for (const c of [...caps]) { c.y += 150*dt;
    if (c.y > raq.y - 8 && c.y < raq.y + 20 && Math.abs(c.x - raq.x) < raq.w/2 + 14) { caps.splice(caps.indexOf(c), 1); acorde([660, 990], .07);
      aviso = PODERES[c.k][1] + '!'; avisoT = 1.4;
      if (c.k === 'M') { const ex = []; for (const b of bolas.filter(b => !b.presa).slice(0, 3)) for (const da of [-.35, .35]) { const v = Math.hypot(b.vx, b.vy), a = Math.atan2(b.vy, b.vx) + da;
          ex.push({x: b.x, y: b.y, r: 7, vx: Math.cos(a)*v, vy: Math.sin(a)*v}); } bolas.push(...ex); if (!ex.length) lancar(); }
      else if (c.k === 'V') vidas = Math.min(6, vidas + 1); else efeitos[c.k] = c.k === 'T' ? 9 : 12; }
    else if (c.y > H + 20) caps.splice(caps.indexOf(c), 1); }
  if (efeitos.T > 0) { efeitos.tiroT = (efeitos.tiroT || 0) - dt; if (efeitos.tiroT <= 0) { efeitos.tiroT = .3;
      lasers.push({x: raq.x - raq.w/2 + 6, y: raq.y}, {x: raq.x + raq.w/2 - 6, y: raq.y}); bip(1500, .04, 'sawtooth', .02, -800); } }
  for (const l of [...lasers]) { l.y -= 720*dt; let bateu = l.y < 40;
    for (const t of tijolos) if (l.x > t.x && l.x < t.x + BW && l.y > t.y && l.y < t.y + BH) { quebrar(t); bateu = true; break; }
    if (bateu) lasers.splice(lasers.indexOf(l), 1); }
  if (!tijolos.some(t => t.tipo !== 'metal' || t.hp > 0) || !tijolos.length) {
    nivel++; pontos += 500; acorde([523, 659, 784, 1046, 1318]); aviso = 'NÍVEL ' + nivel + '!'; avisoT = 1.8; gerarNivel(); reiniciarBola(); }
}
function desenhar(){
  ctx.save(); if (tremor > 0) ctx.translate((Math.random() - .5)*tremor*24, (Math.random() - .5)*tremor*24);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0b0620'); g.addColorStop(1, '#041022'); ctx.fillStyle = g; ctx.fillRect(-20, -20, W + 40, H + 40);
  ctx.strokeStyle = 'rgba(120,90,255,.08)'; ctx.lineWidth = 1;
  for (let x = 0; x < W; x += 32) { ctx.beginPath(); ctx.moveTo(x, 40); ctx.lineTo(x, H); ctx.stroke(); }
  for (let y = 40; y < H; y += 32) { ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke(); }
  for (const t of tijolos) { const cor = corTijolo(t);
    const gt = ctx.createLinearGradient(t.x, t.y, t.x, t.y + BH); gt.addColorStop(0, cor); gt.addColorStop(1, 'rgba(0,0,0,.35)');
    ctx.fillStyle = cor; rr(t.x, t.y, BW, BH, 4); ctx.fill(); ctx.fillStyle = gt; ctx.fill();
    ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.fillRect(t.x + 3, t.y + 2, BW - 6, 3);
    if (t.tipo === 'bomba') { ctx.fillStyle = '#fff'; ctx.font = 'bold 13px system-ui'; ctx.textAlign = 'center'; ctx.fillText('✸', t.x + BW/2, t.y + 14); }
    if (t.tipo === 'metal' && t.hp < t.max) { ctx.strokeStyle = 'rgba(0,0,0,.5)'; ctx.beginPath(); ctx.moveTo(t.x + 8, t.y + 3); ctx.lineTo(t.x + 22, t.y + 15); ctx.lineTo(t.x + 34, t.y + 5); ctx.stroke(); } }
  for (const c of caps) { ctx.shadowColor = PODERES[c.k][0]; ctx.shadowBlur = 14; ctx.fillStyle = PODERES[c.k][0]; rr(c.x - 15, c.y - 8, 30, 16, 8); ctx.fill();
    ctx.shadowBlur = 0; ctx.fillStyle = '#111'; ctx.font = 'bold 12px system-ui'; ctx.textAlign = 'center'; ctx.fillText(c.k, c.x, c.y + 4); }
  ctx.fillStyle = '#ff5ea8'; for (const l of lasers) ctx.fillRect(l.x - 2, l.y - 10, 4, 14);
  if (raq) { ctx.shadowColor = efeitos.T > 0 ? '#ff5ea8' : '#7df9ff'; ctx.shadowBlur = 18;
    const gr = ctx.createLinearGradient(raq.x - raq.w/2, 0, raq.x + raq.w/2, 0); gr.addColorStop(0, '#4f7cff'); gr.addColorStop(.5, '#7df9ff'); gr.addColorStop(1, '#a855f7');
    ctx.fillStyle = gr; rr(raq.x - raq.w/2, raq.y, raq.w, raq.h, 6); ctx.fill(); ctx.shadowBlur = 0; }
  for (const b of bolas || []) { ctx.shadowColor = '#fff'; ctx.shadowBlur = 16; ctx.fillStyle = efeitos.S > 0 ? '#ffd34d' : '#fff';
    ctx.beginPath(); ctx.arc(b.x, b.y, b.r, 0, 7); ctx.fill(); ctx.shadowBlur = 0; }
  for (const p of part) { ctx.globalAlpha = Math.min(1, p.t*2); ctx.fillStyle = p.cor; ctx.fillRect(p.x - 2, p.y - 2, 4, 4); } ctx.globalAlpha = 1;
  ctx.restore();
  ctx.fillStyle = 'rgba(0,0,0,.35)'; ctx.fillRect(0, 0, W, 40);
  if (avisoT > 0) { ctx.globalAlpha = Math.min(1, avisoT); ctx.font = 'bold 30px system-ui'; ctx.textAlign = 'center'; ctx.fillStyle = '#ffd34d'; ctx.fillText(aviso, W/2, H/2 + 60); ctx.globalAlpha = 1; }
  if (estado === 'jogando' && bolas.some(b => b.presa)) { ctx.font = '600 15px system-ui'; ctx.textAlign = 'center'; ctx.fillStyle = '#cfd6ff';
    ctx.fillText('ESPAÇO ou toque para lançar', W/2, H/2 + 110); }
  $('hud').innerHTML = '<span>⭐ ' + pontos + (combo > 1 ? ' <small style="color:#ffd34d">x' + Math.min(combo, 10) + '</small>' : '') + '</span><span>🧱 Nível ' + nivel + '</span><span>' + '⚪'.repeat(Math.max(0, vidas)) + '</span>';
}
function rr(x, y, w, h, r){ ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
addEventListener('keydown', e => { teclas[e.code] = true; if (['Space', 'ArrowLeft', 'ArrowRight'].includes(e.code)) e.preventDefault();
  if (e.code === 'Space' || e.code === 'Enter') { if (estado === 'jogando') lancar(); else { const b = $('bj'); if (b) b.click(); } }
  if (e.code === 'KeyP' && (estado === 'jogando' || estado === 'pausa')) { estado = estado === 'pausa' ? 'jogando' : 'pausa'; tela(estado === 'pausa' ? '<h1>⏸️ Pausa</h1><p>Aperte P para continuar</p>' : null); } });
addEventListener('keyup', e => teclas[e.code] = false);
function moverPara(e){ if (!raq) return; const r = cv.getBoundingClientRect(); raq.x = (e.clientX - r.left)/r.width*W; }
cv.addEventListener('pointermove', e => { if (estado === 'jogando') moverPara(e); });
cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); if (estado === 'jogando') { moverPara(e); lancar(); } });
let ult = performance.now();
function loop(t){ const dt = Math.min(.033, (t - ult)/1000); ult = t; atualizar(dt); desenhar(); requestAnimationFrame(loop); }
raq = {x: W/2, y: 604, w: 90, h: 12}; tijolos = []; bolas = []; caps = []; lasers = []; part = []; efeitos = {L: 0, T: 0, S: 0}; gerarNivel();
tela('<h1>🧱 Quebra-Blocos Neon</h1><p>Rebata a bola e destrua todos os blocos!</p><p>🖱️ Mova o mouse/dedo ou use ← → · ESPAÇO/toque lança</p>' +
     '<p>Pegue as cápsulas: <b style="color:#5be08a">M</b> multibola · <b style="color:#4fc3ff">L</b> larga · <b style="color:#ff5ea8">T</b> laser · <b style="color:#ffd34d">S</b> lenta · <b style="color:#ff4d4d">V</b> vida</p>' +
     '<p>✸ blocos-bomba explodem os vizinhos · 🔩 metal aguenta 4 golpes</p><p>🏆 Recorde: ' + recorde + '</p><button id="bj">▶️ Jogar</button>');
$('bj').onclick = comecar; requestAnimationFrame(loop);
"""

# ---------------------------------------------------------------- BLOCOS CAINDO
CAINDO_JS = r"""
const W = 440, H = 590, cv = $('c'), ctx = cv.getContext('2d'); cv.width = W; cv.height = H;
const C = 10, L = 20, T = 26, OX = 12, OY = 40;
const FORMAS = {I: [[0,0,0,0],[1,1,1,1],[0,0,0,0],[0,0,0,0]], O: [[1,1],[1,1]], T: [[0,1,0],[1,1,1],[0,0,0]],
  S: [[0,1,1],[1,1,0],[0,0,0]], Z: [[1,1,0],[0,1,1],[0,0,0]], J: [[1,0,0],[1,1,1],[0,0,0]], L: [[0,0,1],[1,1,1],[0,0,0]]};
const CORES = {I: '#22d3ee', O: '#facc15', T: '#a855f7', S: '#22c55e', Z: '#ef4444', J: '#3b82f6', L: '#f97316'};
let grade, peca, fila, saco, guardada, podeGuardar, pontos, linhas, nivel, quedaT, travaT, movsTrava, estado = 'inicio', limpando = null, part = [], flutua = [], tremor = 0;
let recorde = lerRecorde('rec_caindo'); const rep = {};
function proximaDoSaco(){ if (!saco.length) saco = embaralhar(Object.keys(FORMAS)); return saco.pop(); }
function nova(tipo){ const m = FORMAS[tipo].map(r => r.slice()); return {tipo, m, x: Math.floor((C - m.length)/2), y: tipo === 'I' ? -1 : 0}; }
function girar(m, dir){ return dir > 0 ? m[0].map((_, i) => m.map(r => r[i]).reverse()) : m[0].map((_, i) => m.map(r => r[r.length - 1 - i])); }
function colide(m, x, y){ for (let r = 0; r < m.length; r++) for (let c = 0; c < m[r].length; c++) if (m[r][c]) {
  const gx = x + c, gy = y + r; if (gx < 0 || gx >= C || gy >= L || (gy >= 0 && grade[gy][gx])) return true; } return false; }
function intervalo(){ return Math.max(.03, Math.pow(.8 - (nivel - 1)*.007, nivel - 1)); }
function comecar(){ grade = Array.from({length: L}, () => Array(C).fill(null)); saco = []; fila = [proximaDoSaco(), proximaDoSaco(), proximaDoSaco()];
  guardada = null; pontos = 0; linhas = 0; nivel = 1; part = []; flutua = []; limpando = null; trocar(); estado = 'jogando'; tela(null); audio(); cv.focus(); }
function trocar(tipo){ peca = nova(tipo || fila.shift()); if (!tipo) fila.push(proximaDoSaco()); podeGuardar = tipo ? false : true; quedaT = 0; travaT = 0; movsTrava = 0;
  if (colide(peca.m, peca.x, peca.y)) { estado = 'fim'; recorde = salvarRecorde('rec_caindo', pontos); ruido(.8, .2); vibrar(300);
    tela('<h1>🧱 Fim de jogo</h1><p class="grande">⭐ ' + pontos + '</p><p>' + linhas + ' linhas · nível ' + nivel + ' · recorde ' + recorde + '</p><button id="bj">🔁 Jogar de novo</button>'); $('bj').onclick = comecar; } }
function mover(dx){ if (!colide(peca.m, peca.x + dx, peca.y)) { peca.x += dx; resetTrava(); bip(380, .02, 'sine', .025); return true; } return false; }
function resetTrava(){ if (colide(peca.m, peca.x, peca.y + 1) && movsTrava < 15) { travaT = 0; movsTrava++; } }
function rodar(dir){ const m = girar(peca.m, dir);
  for (const [dx, dy] of [[0, 0], [-1, 0], [1, 0], [-2, 0], [2, 0], [0, -1], [-1, -1], [1, -1]]) if (!colide(m, peca.x + dx, peca.y + dy)) {
    peca.m = m; peca.x += dx; peca.y += dy; resetTrava(); bip(620, .03, 'triangle', .035); return; } }
function sombraY(){ let y = peca.y; while (!colide(peca.m, peca.x, y + 1)) y++; return y; }
function travar(){ peca.m.forEach((r, i) => r.forEach((v, j) => { if (v && peca.y + i >= 0) grade[peca.y + i][peca.x + j] = CORES[peca.tipo]; }));
  bip(160, .06, 'square', .04);
  const cheias = []; grade.forEach((r, i) => { if (r.every(c => c)) cheias.push(i); });
  if (cheias.length) { limpando = {linhas: cheias, t: .22}; const n = cheias.length;
    const ganho = [0, 100, 300, 500, 800][n]*nivel; pontos += ganho; linhas += n; nivel = 1 + Math.floor(linhas/10);
    flutua.push({txt: ['', 'Simples', 'Dupla!', 'TRIPLA!', 'QUÁDRUPLA!!'][n] + ' +' + ganho, t: 1.4});
    cheias.forEach(y => { for (let x = 0; x < C; x++) for (let k = 0; k < 3; k++) part.push({x: OX + x*T + T/2, y: OY + y*T + T/2, vx: (Math.random() - .5)*420, vy: -Math.random()*300, t: .8, cor: grade[y][x]}); });
    acorde(n >= 4 ? [523, 659, 784, 1046, 1318] : [523 + n*60, 659 + n*60], .1); if (n >= 4) { tremor = .35; vibrar(150); } }
  if (estado === 'jogando') trocar(); }
function queda(){ if (!colide(peca.m, peca.x, peca.y + 1)) { peca.y++; return true; } return false; }
function largar(){ const y0 = peca.y; peca.y = sombraY(); pontos += 2*(peca.y - y0); tremor = .12; travar(); }
function guardar(){ if (!podeGuardar) return; const t = peca.tipo; if (guardada) trocar(guardada); else trocar(); guardada = t; podeGuardar = false; bip(900, .05, 'sine', .04); }
const ACOES = {ArrowLeft: 'esq', KeyA: 'esq', ArrowRight: 'dir', KeyD: 'dir', ArrowDown: 'baixo', KeyS: 'baixo', ArrowUp: 'gira', KeyX: 'gira', KeyW: 'gira',
  KeyZ: 'antigira', Space: 'larga', KeyC: 'guarda', ShiftLeft: 'guarda', ShiftRight: 'guarda', KeyP: 'pausa', Enter: 'inicio'};
function apertar(a){ if (estado === 'inicio' || estado === 'fim') { if (a === 'larga' || a === 'inicio') { const b = $('bj'); if (b) b.click(); } return; }
  if (a === 'pausa') { estado = estado === 'pausa' ? 'jogando' : 'pausa'; tela(estado === 'pausa' ? '<h1>⏸️ Pausa</h1><p>Aperte P para continuar</p>' : null); return; }
  if (estado !== 'jogando' || limpando) return;
  if (a === 'esq' || a === 'dir') { mover(a === 'esq' ? -1 : 1); rep[a] = {t: .16}; }
  else if (a === 'baixo') rep.baixo = {t: 0};
  else if (a === 'gira') rodar(1); else if (a === 'antigira') rodar(-1); else if (a === 'larga') largar(); else if (a === 'guarda') guardar(); }
function soltar(a){ delete rep[a]; }
addEventListener('keydown', e => { const a = ACOES[e.code]; if (!a) return; e.preventDefault(); if (e.repeat) return; apertar(a); });
addEventListener('keyup', e => { const a = ACOES[e.code]; if (a) soltar(a); });
document.querySelectorAll('[data-a]').forEach(b => { const a = b.dataset.a;
  b.addEventListener('pointerdown', e => { e.preventDefault(); b.setPointerCapture(e.pointerId); apertar(a); });
  ['pointerup', 'pointercancel', 'lostpointercapture'].forEach(t => b.addEventListener(t, () => soltar(a))); });
cv.addEventListener('pointerdown', () => { cv.focus(); if (estado !== 'jogando') apertar('inicio'); });
function atualizar(dt){
  for (const p of part) { p.x += p.vx*dt; p.y += p.vy*dt; p.vy += 900*dt; p.t -= dt; } part = part.filter(p => p.t > 0);
  for (const f of flutua) f.t -= dt; flutua = flutua.filter(f => f.t > 0); tremor = Math.max(0, tremor - dt);
  if (estado !== 'jogando') return;
  if (limpando) { limpando.t -= dt; if (limpando.t <= 0) { const ls = limpando.linhas; grade = grade.filter((_, i) => !ls.includes(i));
      while (grade.length < L) grade.unshift(Array(C).fill(null)); limpando = null; } return; }
  for (const a of ['esq', 'dir']) if (rep[a]) { rep[a].t -= dt; while (rep[a] && rep[a].t <= 0) { rep[a].t += .045; if (!mover(a === 'esq' ? -1 : 1)) break; } }
  const intv = rep.baixo ? Math.min(.035, intervalo()) : intervalo();
  quedaT += dt; while (quedaT >= intv) { quedaT -= intv; if (queda()) { if (rep.baixo) pontos++; } else break; }
  if (colide(peca.m, peca.x, peca.y + 1)) { travaT += dt; if (travaT >= .5) travar(); } else travaT = 0;
}
function bloco(x, y, cor, tam = T, alfa = 1){ ctx.globalAlpha = alfa; const g = ctx.createLinearGradient(x, y, x + tam, y + tam);
  g.addColorStop(0, cor); g.addColorStop(1, 'rgba(0,0,0,.45)'); ctx.fillStyle = cor; ctx.fillRect(x + 1, y + 1, tam - 2, tam - 2); ctx.fillStyle = g; ctx.fillRect(x + 1, y + 1, tam - 2, tam - 2);
  ctx.fillStyle = 'rgba(255,255,255,.35)'; ctx.fillRect(x + 3, y + 3, tam - 6, Math.max(2, tam*.14)); ctx.globalAlpha = 1; }
function mini(tipo, x, y, tam){ if (!tipo) return; const m = FORMAS[tipo]; const w = m[0].length*tam;
  m.forEach((r, i) => r.forEach((v, j) => { if (v) bloco(x + j*tam - w/2, y + i*tam, CORES[tipo], tam); })); }
function desenhar(){
  ctx.save(); if (tremor > 0) ctx.translate(0, (Math.random() - .3)*tremor*30);
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0d0a24'); g.addColorStop(1, '#050812'); ctx.fillStyle = g; ctx.fillRect(0, -40, W, H + 80);
  ctx.fillStyle = '#0a0f22'; ctx.fillRect(OX, OY, C*T, L*T); ctx.strokeStyle = 'rgba(120,140,255,.08)';
  for (let x = 0; x <= C; x++) { ctx.beginPath(); ctx.moveTo(OX + x*T, OY); ctx.lineTo(OX + x*T, OY + L*T); ctx.stroke(); }
  for (let y = 0; y <= L; y++) { ctx.beginPath(); ctx.moveTo(OX, OY + y*T); ctx.lineTo(OX + C*T, OY + y*T); ctx.stroke(); }
  ctx.strokeStyle = '#4f7cff'; ctx.lineWidth = 2; ctx.shadowColor = '#4f7cff'; ctx.shadowBlur = 12; ctx.strokeRect(OX - 1, OY - 1, C*T + 2, L*T + 2); ctx.shadowBlur = 0; ctx.lineWidth = 1;
  if (grade) grade.forEach((r, y) => r.forEach((c, x) => { if (c) bloco(OX + x*T, OY + y*T, limpando && limpando.linhas.includes(y) ? '#ffffff' : c); }));
  if (peca && estado !== 'inicio') { const sy = sombraY();
    peca.m.forEach((r, i) => r.forEach((v, j) => { if (v && sy + i >= 0) { ctx.strokeStyle = CORES[peca.tipo]; ctx.globalAlpha = .5; ctx.strokeRect(OX + (peca.x + j)*T + 2, OY + (sy + i)*T + 2, T - 4, T - 4); ctx.globalAlpha = 1; } }));
    peca.m.forEach((r, i) => r.forEach((v, j) => { if (v && peca.y + i >= 0) bloco(OX + (peca.x + j)*T, OY + (peca.y + i)*T, CORES[peca.tipo]); })); }
  for (const p of part) { ctx.globalAlpha = Math.min(1, p.t*1.5); ctx.fillStyle = p.cor || '#fff'; ctx.fillRect(p.x - 3, p.y - 3, 6, 6); } ctx.globalAlpha = 1;
  ctx.restore();
  const px = OX + C*T + 22, cx = px + (W - px - 10)/2;
  ctx.textAlign = 'center'; ctx.fillStyle = '#9fb3ff'; ctx.font = 'bold 13px system-ui';
  ctx.fillText('PRÓXIMAS', cx, OY + 10); if (fila) fila.forEach((t, i) => mini(t, cx, OY + 24 + i*62, 15));
  ctx.fillText('GUARDADA (C)', cx, OY + 222); mini(guardada, cx, OY + 236, 15);
  const st = [['PONTOS', pontos], ['NÍVEL', nivel], ['LINHAS', linhas], ['RECORDE', Math.max(recorde, pontos)]];
  st.forEach(([k, v], i) => { ctx.fillStyle = '#9fb3ff'; ctx.font = 'bold 12px system-ui'; ctx.fillText(k, cx, OY + 320 + i*52);
    ctx.fillStyle = '#fff'; ctx.font = 'bold 22px system-ui'; ctx.fillText(v || 0, cx, OY + 343 + i*52); });
  for (const f of flutua) { ctx.globalAlpha = Math.min(1, f.t); ctx.fillStyle = '#ffd34d'; ctx.font = 'bold 26px system-ui'; ctx.fillText(f.txt, OX + C*T/2, OY + L*T/2 - (1.4 - f.t)*60); } ctx.globalAlpha = 1;
  $('hud').innerHTML = '';
}
let ult = performance.now();
function loop(t){ const dt = Math.min(.05, (t - ult)/1000); ult = t; atualizar(dt); desenhar(); requestAnimationFrame(loop); }
grade = Array.from({length: L}, () => Array(C).fill(null)); saco = []; fila = ['T', 'I', 'L'];
tela('<h1>🟪 Blocos Caindo</h1><p>Encaixe as peças e complete linhas para fazê-las sumir. Fica mais rápido a cada 10 linhas!</p>' +
     '<p>⬅️➡️ move · ⬆️/X gira · Z gira ao contrário · ⬇️ desce rápido · ESPAÇO larga · C guarda</p><p>📱 Use os botões abaixo</p>' +
     '<p>🏆 Recorde: ' + recorde + '</p><button id="bj">▶️ Jogar</button>');
$('bj').onclick = comecar; requestAnimationFrame(loop);
"""

TELA_DIV = "<div class='tela' id='tela'></div>"
TECH = {
    "galaxia": (480, 700, GALAXIA_JS, True, ""),
    "runner": (480, 760, RUNNER_JS, True,
               '<button data-a="esq">⬅️</button><button data-a="pula">⬆️ Pula</button><button data-a="abaixa">⬇️ Desliza</button><button data-a="dir">➡️</button>'),
    "labirinto": (480, 720, LABIRINTO_JS, True, '<button id="bgiro">📱 Usar giroscópio do celular</button>'),
    "quebra": (480, 700, BLOCOS_NEON_JS, False, ""),
    "caindo": (440, 730, CAINDO_JS, False,
               '<button data-a="esq">◀</button><button data-a="gira">⟳</button><button data-a="baixo">▼</button>'
               '<button data-a="larga">⤓</button><button data-a="guarda">⇄</button><button data-a="dir">▶</button>'),
}


def jogo_tech(nome):
    largura, altura, js, tres_d, botoes = TECH[nome]
    jogo_html(pagina_tech(largura, TELA_DIV, js, botoes, tres_d), altura)
    st.caption("🖱️ No computador, clique no jogo antes de usar o teclado. "
               + ("🌐 Jogo 3D em WebGL: precisa de internet para carregar o motor gráfico." if tres_d else ""))


# =====================================================================
# ✨ JOGOS DE OUTRO MUNDO (shaders, raymarching, música procedural, gravidade)
# =====================================================================

# ---------------------------------------------------------------- PORTAL CÓSMICO
PORTAL_JS = SEM_3D + r"""
const W = 480, H = 640, cv = $('c');
const ren = new THREE.WebGLRenderer({canvas: cv, antialias: true}); ren.setPixelRatio(Math.min(2, devicePixelRatio)); ren.setSize(W, H, false);
const cena = new THREE.Scene(); cena.fog = new THREE.FogExp2(0x000000, .004);
const cam = new THREE.PerspectiveCamera(75, W/H, .1, 600); cam.position.set(0, 0, 9);
const uni = {tempo: {value: 0}, vel: {value: 1}, matiz: {value: 0}};
const tunel = new THREE.Mesh(new THREE.CylinderGeometry(11, 11, 700, 72, 1, true), new THREE.ShaderMaterial({
  uniforms: uni, side: THREE.BackSide, depthWrite: false,
  vertexShader: 'varying vec2 vUv; varying float vProf; void main(){ vUv = uv; vec4 mv = modelViewMatrix*vec4(position,1.); vProf = -mv.z; gl_Position = projectionMatrix*mv; }',
  fragmentShader: `varying vec2 vUv; varying float vProf; uniform float tempo, vel, matiz;
    vec3 paleta(float t){ return .5 + .5*cos(6.2831*(vec3(.0,.33,.67) + t + matiz)); }
    void main(){
      float a = vUv.x*6.2831, z = vUv.y*70. + tempo*vel*3.;
      float faixas = sin(z*2. + sin(a*3. + tempo)*1.5)*.5 + .5;
      float espiral = sin(a*6. + z*.8 - tempo*2.)*.5 + .5;
      float aneis = pow(abs(sin(z*.35)), 40.);
      vec3 c = paleta(z*.02 + espiral*.15)*(.25 + faixas*.55) + aneis*vec3(1.,.9,1.)*.9;
      c += pow(espiral, 8.)*paleta(z*.05 + .5)*.6;
      float fundo = exp(-vProf*.0055)*1.25;
      gl_FragColor = vec4(c*fundo, 1.); }`
}));
tunel.rotation.x = Math.PI/2; tunel.position.z = -330; cena.add(tunel);
// orbe do jogador com halo
const orbe = new THREE.Group();
orbe.add(new THREE.Mesh(new THREE.SphereGeometry(.55, 24, 16), new THREE.MeshBasicMaterial({color: 0xffffff})));
const halo = new THREE.Mesh(new THREE.SphereGeometry(1.1, 24, 16), new THREE.MeshBasicMaterial({color: 0x7df9ff, transparent: true, opacity: .35, blending: THREE.AdditiveBlending, depthWrite: false}));
orbe.add(halo); cena.add(orbe);
const NR = 160, rastroPos = new Float32Array(NR*3), rastroG = new THREE.BufferGeometry();
rastroG.setAttribute('position', new THREE.BufferAttribute(rastroPos, 3));
const cTex = document.createElement('canvas'); cTex.width = cTex.height = 32; { const g2 = cTex.getContext('2d'), rg = g2.createRadialGradient(16, 16, 0, 16, 16, 16); rg.addColorStop(0, '#fff'); rg.addColorStop(1, 'rgba(255,255,255,0)'); g2.fillStyle = rg; g2.fillRect(0, 0, 32, 32); }
cena.add(new THREE.Points(rastroG, new THREE.PointsMaterial({map: new THREE.CanvasTexture(cTex), color: 0x7df9ff, size: .3, transparent: true, opacity: .7, blending: THREE.AdditiveBlending, depthWrite: false})));
let rastroI = 0;
const gAnel = new THREE.TorusGeometry(2.3, .16, 12, 48), gCristal = new THREE.OctahedronGeometry(1, 0);
let pontosF = 0, objs = [], estado = 'inicio', energia = 3, pontos = 0, combo = 0, vel = 55, tempo = 0, spawnT = 0, alvo = {x: 0, y: 0}, invul = 0, tremor = 0, nivel = 1;
let recorde = lerRecorde('rec_portal'); const teclas = {};
const ESCALA = [261.6, 293.7, 329.6, 392, 440, 523.3, 587.3, 659.3, 784, 880];
let pad = null;
function ligarPad(){ const a = audio(); if (!a || pad) return; const g = a.createGain(); g.gain.value = mudo ? 0 : .035; g.connect(a.destination);
  pad = {g, osc: [130.8, 196, 261.6, 329.6].map((f, i) => { const o = a.createOscillator(); o.type = i % 2 ? 'sine' : 'triangle'; o.frequency.value = f; o.detune.value = (i - 1.5)*6; o.connect(g); o.start(); return o; })}; }
setInterval(() => { if (pad) pad.g.gain.value = mudo || estado !== 'jogando' ? 0 : .035; }, 200);
function hud(){ $('hud').innerHTML = '<span>✨ ' + pontos + '</span><span>' + (combo > 1 ? '🔥 x' + combo : '🌀 Nível ' + nivel) + '</span><span>' + '💠'.repeat(Math.max(0, energia)) + '</span>'; }
function gerar(){ const r = Math.random()*6.2, d = Math.random()*6.5;
  if (Math.random() < .55) { const m = new THREE.Mesh(gAnel, new THREE.MeshBasicMaterial({color: new THREE.Color().setHSL(Math.random(), 1, .6)}));
    m.position.set(Math.cos(r)*d, Math.sin(r)*d, -420); m.userData = {tipo: 'anel'}; cena.add(m); objs.push(m); }
  else { const n = 1 + Math.floor(Math.random()*Math.min(4, nivel + 1));
    for (let k = 0; k < n; k++) { const ang = Math.random()*6.2, dd = Math.random()*7.5;
      const m = new THREE.Mesh(gCristal, new THREE.MeshBasicMaterial({color: 0xff2e88, wireframe: Math.random() < .3}));
      m.scale.set(.8, 2.2, .8); m.position.set(Math.cos(ang)*dd, Math.sin(ang)*dd, -420 - k*14); m.userData = {tipo: 'cristal', giro: Math.random()*4 - 2}; cena.add(m); objs.push(m); } } }
function comecar(){ objs.forEach(o => cena.remove(o)); objs = []; energia = 3; pontos = 0; combo = 0; vel = 55; tempo = 0; nivel = 1; invul = 0; alvo = {x: 0, y: 0};
  estado = 'jogando'; tela(null); audio(); ligarPad(); cv.focus(); hud(); }
function apontar(e){ const r = cv.getBoundingClientRect(); const nx = ((e.clientX - r.left)/r.width - .5)*2, ny = -((e.clientY - r.top)/r.height - .5)*2;
  alvo.x = nx*8.5; alvo.y = ny*8.5*H/W*.8; }
cv.addEventListener('pointermove', e => { if (estado === 'jogando') apontar(e); });
cv.addEventListener('pointerdown', e => { cv.setPointerCapture(e.pointerId); if (estado === 'jogando') apontar(e); });
addEventListener('keydown', e => { teclas[e.code] = true; if (e.code.startsWith('Arrow') || e.code === 'Space') e.preventDefault();
  if ((e.code === 'Space' || e.code === 'Enter') && estado !== 'jogando') { const b = $('bj'); if (b) b.click(); } });
addEventListener('keyup', e => teclas[e.code] = false);
let ult = performance.now();
function loop(t){ const dt = Math.min(.04, (t - ult)/1000); ult = t; requestAnimationFrame(loop);
  uni.tempo.value += dt; const jogando = estado === 'jogando';
  if (jogando) {
    tempo += dt; vel = Math.min(140, 55 + tempo*1.3); nivel = 1 + Math.floor(tempo/20); uni.matiz.value = nivel*.13;
    const v = 12*dt; if (teclas.ArrowLeft || teclas.KeyA) alvo.x -= v; if (teclas.ArrowRight || teclas.KeyD) alvo.x += v;
    if (teclas.ArrowUp || teclas.KeyW) alvo.y += v; if (teclas.ArrowDown || teclas.KeyS) alvo.y -= v;
    const d = Math.hypot(alvo.x, alvo.y); if (d > 8.3) { alvo.x *= 8.3/d; alvo.y *= 8.3/d; }
    orbe.position.x += (alvo.x - orbe.position.x)*Math.min(1, dt*9); orbe.position.y += (alvo.y - orbe.position.y)*Math.min(1, dt*9);
    spawnT -= dt; if (spawnT <= 0) { gerar(); spawnT = Math.max(.32, .9 - tempo*.012); }
    invul = Math.max(0, invul - dt);
    for (const o of [...objs]) { const z0 = o.position.z; o.position.z += vel*dt;
      if (o.userData.tipo === 'anel') { o.rotation.z += dt; o.scale.setScalar(1 + Math.sin(t/150)*.05);
        if (z0 < 0 && o.position.z >= 0) { const dd = Math.hypot(o.position.x - orbe.position.x, o.position.y - orbe.position.y);
          if (dd < 2.1) { combo++; pontos += 100*combo; bip(ESCALA[Math.min(combo - 1, 9)], .35, 'sine', .09); bip(ESCALA[Math.min(combo - 1, 9)]*2, .25, 'triangle', .03);
            halo.material.color.copy(o.material.color); cam.fov = 75 + Math.min(combo, 8)*1.6; cam.updateProjectionMatrix(); }
          else { combo = 0; bip(180, .12, 'triangle', .04); cam.fov = 75; cam.updateProjectionMatrix(); } hud(); } }
      else { o.rotation.y += o.userData.giro*dt; o.rotation.x += dt;
        if (Math.abs(o.position.z) < 1.2 && invul <= 0 && Math.hypot(o.position.x - orbe.position.x, o.position.y - orbe.position.y) < 1.6) {
          energia--; invul = 1.5; tremor = .5; combo = 0; ruido(.4, .2); vibrar(150); hud();
          if (energia <= 0) { estado = 'fim'; recorde = salvarRecorde('rec_portal', pontos);
            tela('<h1>🌀 O portal te expulsou!</h1><p class="grande">✨ ' + pontos + '</p><p>Nível ' + nivel + ' · Recorde: ' + recorde + '</p><button id="bj">🌀 Entrar de novo</button>'); $('bj').onclick = comecar; } } }
      if (o.position.z > 15) { cena.remove(o); objs.splice(objs.indexOf(o), 1); } }
    pontosF += vel*dt*.3; if (pontosF >= 1) { pontos += Math.floor(pontosF); pontosF -= Math.floor(pontosF); } if (Math.random() < .05) hud();
  } else { orbe.position.x = Math.sin(t/900)*3; orbe.position.y = Math.cos(t/700)*2; }
  uni.vel.value += ((jogando ? vel/40 : .8) - uni.vel.value)*Math.min(1, dt*2);
  halo.scale.setScalar(1 + Math.sin(t/120)*.12); orbe.visible = invul <= 0 || Math.floor(invul*12) % 2 === 0;
  rastroPos.set([orbe.position.x + (Math.random() - .5)*.3, orbe.position.y + (Math.random() - .5)*.3, 0], rastroI*3); rastroI = (rastroI + 1) % NR;
  for (let i = 0; i < NR; i++) rastroPos[i*3 + 2] += (jogando ? vel : 30)*dt*.25; rastroG.attributes.position.needsUpdate = true;
  tremor = Math.max(0, tremor - dt);
  cam.position.x = orbe.position.x*.35 + (Math.random() - .5)*tremor; cam.position.y = orbe.position.y*.35 + (Math.random() - .5)*tremor;
  cam.lookAt(orbe.position.x*.2, orbe.position.y*.2, -40); cam.rotation.z = Math.sin(uni.tempo.value*.3)*.08;
  ren.render(cena, cam);
}
tela('<h1>🌀 Portal Cósmico</h1><p>Voe pelo buraco de minhoca! Passe <b>por dentro dos anéis</b> para fazer combos musicais e desvie dos cristais rosa.</p>' +
     '<p>🖱️ Aponte com o mouse ou o dedo · ⌨️ setas</p><p>🏆 Recorde: ' + recorde + '</p><button id="bj">🌀 Entrar no portal</button>');
$('bj').onclick = comecar; hud(); requestAnimationFrame(loop);
"""

# ---------------------------------------------------------------- ESTILINGUE CÓSMICO
ESTILINGUE_JS = r"""
const W = 480, H = 640, cv = $('c'), ctx = cv.getContext('2d'); cv.width = W; cv.height = H;
const G = 3.2e6;
let nivel = 1, planetas, alvoP, poeiras, cometa, rastro = [], part = [], arrasto = null, tiros = 0, estado = 'inicio', tempo = 0, coletadas = 0;
let melhor = lerRecorde('rec_estilingue'); const estrelas = Array.from({length: 160}, () => ({x: Math.random()*W, y: Math.random()*H, r: Math.random()*1.4 + .2, f: Math.random()*6}));
const CORES = [['#ffb347', '#c0392b'], ['#7df9ff', '#1e3a8a'], ['#c084fc', '#4c1d95'], ['#86efac', '#14532d'], ['#fda4af', '#9f1239'], ['#fde68a', '#92400e']];
function rnd(a, b){ return a + Math.random()*(b - a); }
function gerarNivel(){
  for (let tent = 0; tent < 200; tent++) {
    planetas = []; const n = Math.min(1 + Math.ceil(nivel/2), 5);
    for (let i = 0; i < n; i++) { const r = rnd(22, 42); const p = {x: rnd(110, W - 90), y: rnd(130, H - 150), r, m: r*r*rnd(.8, 1.3), c: CORES[Math.floor(Math.random()*CORES.length)], anel: Math.random() < .35, fase: Math.random()*6};
      if (planetas.every(q => Math.hypot(q.x - p.x, q.y - p.y) > q.r + p.r + 60)) planetas.push(p); }
    alvoP = {x: rnd(W*.55, W - 50), y: rnd(70, 150), r: 22};
    if (Math.random() < .5) { alvoP.y = rnd(H*.35, H*.6); alvoP.x = W - 45; }
    const ini = {x: 55, y: H - 70};
    if (planetas.some(p => Math.hypot(p.x - alvoP.x, p.y - alvoP.y) < p.r + 60 || Math.hypot(p.x - ini.x, p.y - ini.y) < p.r + 80)) continue;
    poeiras = []; for (let k = 0; k < 3; k++) { const q = {x: rnd(60, W - 60), y: rnd(60, H - 120), ok: false};
      if (planetas.every(p => Math.hypot(p.x - q.x, p.y - q.y) > p.r + 25)) poeiras.push(q); }
    break; }
  tiros = 0; coletadas = 0; novoCometa(); }
function novoCometa(){ cometa = {x: 55, y: H - 70, vx: 0, vy: 0, voando: false, t: 0}; rastro = []; poeiras.forEach(p => p.ok = false); coletadas = 0; }
function acel(x, y){ let ax = 0, ay = 0; for (const p of planetas) { const dx = p.x - x, dy = p.y - y, d2 = dx*dx + dy*dy + 400, d = Math.sqrt(d2);
  const f = G*p.m/1000/d2; ax += f*dx/d; ay += f*dy/d; } return [ax, ay]; }
function prever(vx, vy){ const pts = []; let x = cometa.x, y = cometa.y; const dt = 1/60, passos = Math.max(35, 95 - nivel*6);
  for (let i = 0; i < passos; i++) { for (let s = 0; s < 2; s++) { const [ax, ay] = acel(x, y); vx += ax*dt/2; vy += ay*dt/2; x += vx*dt/2; y += vy*dt/2; }
    if (planetas.some(p => Math.hypot(p.x - x, p.y - y) < p.r)) break; pts.push([x, y]); } return pts; }
function explodir(x, y, cor, n = 40){ for (let i = 0; i < n; i++) { const a = Math.random()*6.28, s = rnd(40, 280); part.push({x, y, vx: Math.cos(a)*s, vy: Math.sin(a)*s, t: rnd(.5, 1.2), cor}); } }
function pos(e){ const r = cv.getBoundingClientRect(); return [(e.clientX - r.left)/r.width*W, (e.clientY - r.top)/r.height*H]; }
cv.addEventListener('pointerdown', e => { if (estado !== 'jogando' || cometa.voando) return; cv.setPointerCapture(e.pointerId); const [x, y] = pos(e); arrasto = {x0: x, y0: y, x, y}; audio(); });
cv.addEventListener('pointermove', e => { if (!arrasto) return; const [x, y] = pos(e); arrasto.x = x; arrasto.y = y; });
cv.addEventListener('pointerup', () => { if (!arrasto) return; const [vx, vy] = vetor(); arrasto = null;
  if (Math.hypot(vx, vy) < 40) return; cometa.vx = vx; cometa.vy = vy; cometa.voando = true; tiros++; bip(220, .4, 'sine', .08, 600); });
function vetor(){ if (!arrasto) return [0, 0]; let dx = (arrasto.x0 - arrasto.x)*3.2, dy = (arrasto.y0 - arrasto.y)*3.2; const m = Math.hypot(dx, dy), max = 520;
  if (m > max) { dx *= max/m; dy *= max/m; } return [dx, dy]; }
function falhou(msg){ cometa.voando = false; bip(140, .3, 'sawtooth', .06); setTimeout(() => { if (estado === 'jogando') novoCometa(); }, 700); aviso = msg; avisoT = 1.2; }
let aviso = '', avisoT = 0;
function venceu(){ estado = 'venceu'; const est = (tiros <= 1 ? 2 : tiros <= 3 ? 1 : 0) + (coletadas === poeiras.length ? 1 : 0);
  melhor = salvarRecorde('rec_estilingue', nivel); acorde([392, 523, 659, 784, 1046], .15); explodir(alvoP.x, alvoP.y, '#7df9ff', 80);
  setTimeout(() => { tela('<h1>🌟 Nível ' + nivel + ' concluído!</h1><p class="grande">' + '⭐'.repeat(Math.max(1, est)) + '☆'.repeat(3 - Math.max(1, est)) + '</p><p>' + tiros + ' lançamento(s) · ✨ ' + coletadas + '/' + poeiras.length + ' poeiras estelares</p><button id="bj">🚀 Próximo nível</button>');
    $('bj').onclick = () => { nivel++; gerarNivel(); estado = 'jogando'; tela(null); }; }, 900); }
function atualizar(dt){ tempo += dt; avisoT -= dt;
  for (const p of part) { p.x += p.vx*dt; p.y += p.vy*dt; p.vx *= .98; p.vy *= .98; p.t -= dt; } part = part.filter(p => p.t > 0);
  if (estado !== 'jogando' || !cometa.voando) return;
  const sub = 4; for (let s = 0; s < sub; s++) { const h = dt/sub; const [ax, ay] = acel(cometa.x, cometa.y);
    cometa.vx += ax*h; cometa.vy += ay*h; cometa.x += cometa.vx*h; cometa.y += cometa.vy*h; }
  cometa.t += dt; rastro.push([cometa.x, cometa.y]); if (rastro.length > 70) rastro.shift();
  if (Math.random() < .7) part.push({x: cometa.x, y: cometa.y, vx: rnd(-20, 20) - cometa.vx*.1, vy: rnd(-20, 20) - cometa.vy*.1, t: .5, cor: '#9fe6ff'});
  for (const p of poeiras) if (!p.ok && Math.hypot(p.x - cometa.x, p.y - cometa.y) < 18) { p.ok = true; coletadas++; bip(1046 + coletadas*200, .25, 'sine', .07); explodir(p.x, p.y, '#ffe066', 18); }
  for (const p of planetas) if (Math.hypot(p.x - cometa.x, p.y - cometa.y) < p.r + 4) { explodir(cometa.x, cometa.y, p.c[0], 50); ruido(.4, .18); falhou('💥 Colidiu com o planeta!'); return; }
  if (Math.hypot(alvoP.x - cometa.x, alvoP.y - cometa.y) < alvoP.r + 6) { cometa.voando = false; venceu(); return; }
  if (cometa.x < -150 || cometa.x > W + 150 || cometa.y < -150 || cometa.y > H + 150 || cometa.t > 12) falhou('🌌 Perdido no espaço…'); }
function desenhar(){
  const g = ctx.createRadialGradient(W*.3, H*.3, 20, W*.5, H*.5, H*.8); g.addColorStop(0, '#1c0f3d'); g.addColorStop(.6, '#0a0820'); g.addColorStop(1, '#03030b');
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  [['rgba(168,85,247,.10)', W*.75, H*.25, 180], ['rgba(56,189,248,.08)', W*.2, H*.7, 200], ['rgba(244,114,182,.07)', W*.6, H*.85, 150]].forEach(([c, x, y, r]) => {
    const n = ctx.createRadialGradient(x, y, 0, x, y, r); n.addColorStop(0, c); n.addColorStop(1, 'transparent'); ctx.fillStyle = n; ctx.fillRect(0, 0, W, H); });
  for (const s of estrelas) { ctx.globalAlpha = .4 + .6*Math.abs(Math.sin(tempo*1.5 + s.f)); ctx.fillStyle = '#fff'; ctx.fillRect(s.x, s.y, s.r, s.r); } ctx.globalAlpha = 1;
  // portal de chegada
  ctx.save(); ctx.translate(alvoP.x, alvoP.y);
  for (let i = 0; i < 4; i++) { ctx.rotate(tempo*(1 + i*.3)); ctx.strokeStyle = `hsla(${180 + i*30},100%,70%,${.8 - i*.15})`; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(0, 0, alvoP.r - i*4, 0, 4.2); ctx.stroke(); }
  const pg = ctx.createRadialGradient(0, 0, 0, 0, 0, alvoP.r*1.8); pg.addColorStop(0, 'rgba(125,249,255,.6)'); pg.addColorStop(1, 'transparent'); ctx.fillStyle = pg; ctx.beginPath(); ctx.arc(0, 0, alvoP.r*1.8, 0, 7); ctx.fill();
  ctx.restore();
  for (const p of planetas) {
    const gr = ctx.createRadialGradient(p.x, p.y, p.r*.5, p.x, p.y, p.r*2.4); gr.addColorStop(0, p.c[0] + '30'); gr.addColorStop(1, 'transparent'); ctx.fillStyle = gr; ctx.beginPath(); ctx.arc(p.x, p.y, p.r*2.4, 0, 7); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.06)'; ctx.setLineDash([3, 6]); ctx.beginPath(); ctx.arc(p.x, p.y, p.r*2.2, 0, 7); ctx.stroke(); ctx.setLineDash([]);
    if (p.anel) { ctx.strokeStyle = p.c[0] + '99'; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(p.x, p.y, p.r*1.7, p.r*.45, -.35, Math.PI, 2*Math.PI); ctx.stroke(); }
    const ps = ctx.createRadialGradient(p.x - p.r*.4, p.y - p.r*.4, p.r*.1, p.x, p.y, p.r); ps.addColorStop(0, p.c[0]); ps.addColorStop(1, p.c[1]);
    ctx.fillStyle = ps; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fill();
    ctx.strokeStyle = 'rgba(255,255,255,.15)'; ctx.lineWidth = 2; for (let k = -1; k <= 1; k++) { ctx.beginPath(); ctx.ellipse(p.x, p.y + k*p.r*.35, p.r*.95, p.r*.12, 0, 0, 7); ctx.stroke(); }
    if (p.anel) { ctx.strokeStyle = p.c[0] + 'cc'; ctx.lineWidth = 4; ctx.beginPath(); ctx.ellipse(p.x, p.y, p.r*1.7, p.r*.45, -.35, 0, Math.PI); ctx.stroke(); } ctx.lineWidth = 1; }
  for (const p of poeiras) if (!p.ok) { const s = 7 + Math.sin(tempo*4 + p.x)*2; ctx.fillStyle = '#ffe066'; ctx.shadowColor = '#ffe066'; ctx.shadowBlur = 14;
    ctx.beginPath(); for (let i = 0; i < 10; i++) { const a = i*Math.PI/5 - Math.PI/2, r = i % 2 ? s*.45 : s; ctx.lineTo(p.x + Math.cos(a)*r, p.y + Math.sin(a)*r); } ctx.fill(); ctx.shadowBlur = 0; }
  if (arrasto && !cometa.voando) { const [vx, vy] = vetor(); const pts = prever(vx, vy);
    pts.forEach(([x, y], i) => { if (i % 3) return; ctx.globalAlpha = 1 - i/pts.length; ctx.fillStyle = '#9fe6ff'; ctx.beginPath(); ctx.arc(x, y, 2.4, 0, 7); ctx.fill(); }); ctx.globalAlpha = 1;
    ctx.strokeStyle = 'rgba(255,94,168,.8)'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(cometa.x, cometa.y); ctx.lineTo(cometa.x - vx/8, cometa.y - vy/8); ctx.stroke(); ctx.lineWidth = 1; }
  rastro.forEach(([x, y], i) => { ctx.globalAlpha = i/rastro.length*.8; ctx.fillStyle = '#7df9ff'; ctx.beginPath(); ctx.arc(x, y, 1 + i/rastro.length*4, 0, 7); ctx.fill(); }); ctx.globalAlpha = 1;
  for (const p of part) { ctx.globalAlpha = Math.min(1, p.t*2); ctx.fillStyle = p.cor; ctx.fillRect(p.x - 1.5, p.y - 1.5, 3, 3); } ctx.globalAlpha = 1;
  if (estado !== 'venceu') { ctx.shadowColor = '#fff'; ctx.shadowBlur = 20; ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(cometa.x, cometa.y, 7, 0, 7); ctx.fill(); ctx.shadowBlur = 0; }
  if (!cometa.voando && !arrasto && estado === 'jogando') { ctx.strokeStyle = `rgba(255,255,255,${.4 + Math.sin(tempo*4)*.3})`; ctx.beginPath(); ctx.arc(cometa.x, cometa.y, 16 + Math.sin(tempo*4)*3, 0, 7); ctx.stroke(); }
  if (avisoT > 0) { ctx.globalAlpha = Math.min(1, avisoT*2); texto2(aviso, W/2, H/2, 22, '#ffd34d'); ctx.globalAlpha = 1; }
  $('hud').innerHTML = '<span>🪐 Nível ' + nivel + '</span><span>🚀 ' + tiros + ' lanç.</span><span>✨ ' + coletadas + '/' + (poeiras ? poeiras.length : 0) + '</span>';
}
function texto2(t, x, y, tam, cor){ ctx.font = `bold ${tam}px system-ui`; ctx.textAlign = 'center'; ctx.fillStyle = cor; ctx.fillText(t, x, y); }
function comecar(){ nivel = 1; gerarNivel(); estado = 'jogando'; tela(null); audio(); }
addEventListener('keydown', e => { if ((e.code === 'Space' || e.code === 'Enter') && estado !== 'jogando') { e.preventDefault(); const b = $('bj'); if (b) b.click(); }
  if (e.code === 'KeyR' && estado === 'jogando') novoCometa(); if (e.code === 'KeyN' && estado === 'jogando' && tiros >= 5) { nivel++; gerarNivel(); } });
let ult = performance.now();
function loop(t){ const dt = Math.min(.033, (t - ult)/1000); ult = t; atualizar(dt); desenhar(); requestAnimationFrame(loop); }
gerarNivel();
tela('<h1>🪐 Estilingue Cósmico</h1><p>Leve o cometa até o <b>portal azul</b> usando a <b>gravidade</b> dos planetas para fazer curvas!</p>' +
     '<p>👆 Arraste para trás (como um estilingue) e solte. A linha pontilhada mostra o começo da trajetória.</p><p>⭐ Menos lançamentos + todas as ✨ poeiras = 3 estrelas</p>' +
     '<p>🏆 Chegou ao nível ' + Math.max(1, melhor) + '</p><button id="bj">🚀 Começar</button>');
$('bj').onclick = comecar; requestAnimationFrame(loop);
"""

# ---------------------------------------------------------------- SINFONIA DAS ESTRELAS
SINFONIA_JS = r"""
const W = 480, H = 640, cv = $('c'), ctx = cv.getContext('2d'); cv.width = W; cv.height = H;
const CORES = ['#ff5ea8', '#ffd34d', '#5be08a', '#7df9ff'], TECLAS = ['KeyD', 'KeyF', 'KeyJ', 'KeyK'], ROT = ['D', 'F', 'J', 'K'];
const HIT_Y = H - 110, VISTA = 1.8;
let estado = 'inicio', musica = 1, notas = [], inicio = 0, bpm, duracao, pontos = 0, combo = 0, maxCombo = 0, acertos = {p: 0, o: 0, b: 0, e: 0}, julg = '', julgT = 0, estrelas = [], brilho = [0, 0, 0, 0], cadentes = [];
let recorde = lerRecorde('rec_sinfonia');
const TONS = [[0, 4, 7], [9, 12, 16], [5, 9, 12], [7, 11, 14], [2, 5, 9], [4, 7, 11]];
const PROGS = [[0, 1, 2, 3], [0, 3, 1, 2], [1, 2, 0, 3], [0, 4, 3, 0], [0, 5, 2, 3]];
function hz(semi, base = 261.63){ return base*Math.pow(2, semi/12); }
function compor(){
  const a = audio(); bpm = Math.min(150, 92 + musica*8); const b = 60/bpm, prog = PROGS[(musica - 1) % PROGS.length], compassos = 16, raiz = [0, 2, 5, 7, -3][musica % 5];
  const escala = [0, 2, 4, 7, 9, 12, 14, 16, 19, 21];
  notas = []; let ult = 4;
  const densidade = Math.min(.85, .42 + musica*.08);
  for (let c = 0; c < compassos; c++) { const acorde = TONS[prog[c % 4]];
    for (let s = 0; s < 8; s++) { const t = (c*4 + s/2)*b; if (c === 0 && s < 4) continue;
      const forte = s % 2 === 0; if (Math.random() > (forte ? densidade + .1 : densidade*.45)) continue;
      let semi; if (forte && Math.random() < .6) semi = acorde[Math.floor(Math.random()*3)] + (Math.random() < .5 ? 12 : 0);
      else { ult = Math.max(0, Math.min(escala.length - 1, ult + Math.floor(Math.random()*5) - 2)); semi = escala[ult]; }
      const lane = Math.min(3, Math.floor(((semi % 24) + 24) % 24/6));
      notas.push({t, lane, f: hz(semi + raiz, 523.25), estado: 0}); } }
  duracao = compassos*4*b + 2;
  inicio = a.currentTime + 2.2;
  if (!mudo) for (let c = 0; c < compassos; c++) { const ac = TONS[prog[c % 4]], t0 = inicio + c*4*b;
    ac.forEach((s, i) => tocar(hz(s + raiz - 12), t0, 4*b*.95, 'triangle', .035));
    for (let k = 0; k < 4; k++) tocar(hz(ac[0] + raiz - 24), t0 + k*b, b*.5, 'sine', .09);
    for (let k = 0; k < 8; k++) tocar(k % 2 ? 7000 : 60, t0 + k*b/2, .04, k % 2 ? 'square' : 'sine', k % 2 ? .006 : .12); }
}
function tocar(f, quando, dur, tipo, vol){ const a = audio(); if (!a) return; const o = a.createOscillator(), g = a.createGain(); o.type = tipo; o.frequency.value = f;
  g.gain.setValueAtTime(0, quando); g.gain.linearRampToValueAtTime(vol, quando + .01); g.gain.exponentialRampToValueAtTime(.0001, quando + dur);
  o.connect(g); g.connect(a.destination); o.start(quando); o.stop(quando + dur + .05); }
function agora(){ return AC ? AC.currentTime - inicio : 0; }
function comecar(){ audio(); pontos = 0; combo = 0; maxCombo = 0; acertos = {p: 0, o: 0, b: 0, e: 0}; estrelas = []; compor(); estado = 'jogando'; tela(null); cv.focus(); }
function bater(lane){ if (estado !== 'jogando') return; brilho[lane] = 1; const t = agora();
  let melhor = null; for (const n of notas) if (n.lane === lane && n.estado === 0 && Math.abs(n.t - t) < .2) { if (!melhor || Math.abs(n.t - t) < Math.abs(melhor.t - t)) melhor = n; }
  if (!melhor) { bip(110, .05, 'sine', .02); return; }
  const d = Math.abs(melhor.t - t); melhor.estado = 1; const a = audio();
  if (!mudo && a) { tocar(melhor.f, a.currentTime, .5, 'triangle', .12); tocar(melhor.f*2, a.currentTime, .3, 'sine', .04); }
  combo++; maxCombo = Math.max(maxCombo, combo); const mult = 1 + Math.floor(combo/10);
  if (d < .055) { acertos.p++; pontos += 300*mult; julg = 'PERFEITO!'; nascerEstrela(lane, true); }
  else if (d < .11) { acertos.o++; pontos += 200*mult; julg = 'ÓTIMO'; nascerEstrela(lane, false); }
  else { acertos.b++; pontos += 100*mult; julg = 'BOM'; }
  julgT = .6; }
function nascerEstrela(lane, grande){ const s = {x: 30 + Math.random()*(W - 60), y: 40 + Math.random()*(HIT_Y - 260), r: grande ? 2.8 : 1.8, c: CORES[lane], t: 0};
  estrelas.push(s); if (estrelas.length > 60) estrelas.shift(); if (Math.random() < .15) cadentes.push({x: Math.random()*W, y: 0, t: 1}); }
addEventListener('keydown', e => { const i = TECLAS.indexOf(e.code); if (i >= 0) { e.preventDefault(); if (!e.repeat) bater(i); }
  if ((e.code === 'Space' || e.code === 'Enter') && estado !== 'jogando') { e.preventDefault(); const b = $('bj'); if (b) b.click(); } });
cv.addEventListener('pointerdown', e => { const r = cv.getBoundingClientRect(); const x = (e.clientX - r.left)/r.width*W; bater(Math.max(0, Math.min(3, Math.floor(x/(W/4))))); });
function laneX(l, prof){ const larg = 70 + (1 - prof)*(W - 100 - 70)/1; const centro = W/2; const total = 40 + (1 - prof)*(W - 60); return centro - total/2 + total*(l + .5)/4; }
function yDe(prof){ return 90 + (1 - prof)*(HIT_Y - 90); }
function desenhar(){
  const t = agora(), b = 60/(bpm || 100), pulso = estado === 'jogando' ? Math.pow(1 - ((t/b) % 1 + 1) % 1, 3) : 0;
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#060418'); g.addColorStop(1, '#170a35'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 70; i++) { const x = (i*97) % W, y = (i*53) % (H - 200); ctx.globalAlpha = .25 + .25*Math.sin(performance.now()/700 + i); ctx.fillStyle = '#fff'; ctx.fillRect(x, y, 1.2, 1.2); } ctx.globalAlpha = 1;
  ctx.strokeStyle = 'rgba(180,200,255,.18)'; ctx.lineWidth = 1; for (let i = 1; i < estrelas.length; i++) { const a = estrelas[i - 1], c = estrelas[i]; if (Math.hypot(a.x - c.x, a.y - c.y) < 170) { ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(c.x, c.y); ctx.stroke(); } }
  for (const s of estrelas) { s.t += .016; const r = s.r*(1 + pulso*.6) + (s.t < .4 ? (.4 - s.t)*20 : 0); ctx.shadowColor = s.c; ctx.shadowBlur = 12; ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(s.x, s.y, r, 0, 7); ctx.fill(); } ctx.shadowBlur = 0;
  for (const c of cadentes) { c.x += 7; c.y += 4; c.t -= .02; ctx.strokeStyle = `rgba(255,255,255,${c.t})`; ctx.beginPath(); ctx.moveTo(c.x, c.y); ctx.lineTo(c.x - 50, c.y - 28); ctx.stroke(); } cadentes = cadentes.filter(c => c.t > 0);
  // estrada
  ctx.beginPath(); ctx.moveTo(laneX(-.5, 1), yDe(1)); ctx.lineTo(laneX(3.5, 1), yDe(1)); ctx.lineTo(laneX(3.5, 0) + 10, yDe(0) + 60); ctx.lineTo(laneX(-.5, 0) - 10, yDe(0) + 60); ctx.closePath();
  const ge = ctx.createLinearGradient(0, 90, 0, H); ge.addColorStop(0, 'rgba(79,124,255,0)'); ge.addColorStop(1, `rgba(79,124,255,${.18 + pulso*.15})`); ctx.fillStyle = ge; ctx.fill();
  for (let l = 0; l <= 4; l++) { ctx.strokeStyle = 'rgba(160,180,255,.25)'; ctx.beginPath(); ctx.moveTo(laneX(l - .5, 1), yDe(1)); ctx.lineTo(laneX(l - .5, 0), yDe(0) + 60); ctx.stroke(); }
  for (let l = 0; l < 4; l++) { brilho[l] = Math.max(0, brilho[l] - .06); const x = laneX(l, 0);
    ctx.strokeStyle = CORES[l]; ctx.lineWidth = 3; ctx.shadowColor = CORES[l]; ctx.shadowBlur = 10 + brilho[l]*30; ctx.beginPath(); ctx.arc(x, HIT_Y, 30 + brilho[l]*6, 0, 7); ctx.stroke(); ctx.shadowBlur = 0; ctx.lineWidth = 1;
    if (brilho[l] > 0) { ctx.globalAlpha = brilho[l]*.5; ctx.fillStyle = CORES[l]; ctx.beginPath(); ctx.moveTo(x - 30, HIT_Y); ctx.lineTo(laneX(l, 1) - 6, yDe(1)); ctx.lineTo(laneX(l, 1) + 6, yDe(1)); ctx.lineTo(x + 30, HIT_Y); ctx.fill(); ctx.globalAlpha = 1; }
    ctx.font = 'bold 16px system-ui'; ctx.textAlign = 'center'; ctx.fillStyle = 'rgba(255,255,255,.55)'; ctx.fillText(ROT[l], x, HIT_Y + 58); }
  if (estado === 'jogando') for (const n of notas) { const dtn = n.t - t; if (n.estado === 0 && dtn < -.2) { n.estado = 2; acertos.e++; combo = 0; julg = 'ERROU'; julgT = .5; }
    if (n.estado !== 0 || dtn > VISTA || dtn < -.2) continue; const prof = Math.max(0, dtn/VISTA), x = laneX(n.lane, prof), y = yDe(prof), r = 7 + (1 - prof)*19;
    ctx.shadowColor = CORES[n.lane]; ctx.shadowBlur = 18; const gn = ctx.createRadialGradient(x - r*.3, y - r*.3, 1, x, y, r); gn.addColorStop(0, '#fff'); gn.addColorStop(1, CORES[n.lane]);
    ctx.fillStyle = gn; ctx.beginPath(); for (let k = 0; k < 8; k++) { const a = k*Math.PI/4 + performance.now()/400, rr = k % 2 ? r*.6 : r; ctx.lineTo(x + Math.cos(a)*rr, y + Math.sin(a)*rr*.8); } ctx.fill(); ctx.shadowBlur = 0; }
  julgT -= .016; if (julgT > 0) { ctx.globalAlpha = Math.min(1, julgT*2); ctx.font = 'bold 30px system-ui'; ctx.textAlign = 'center';
    ctx.fillStyle = julg === 'PERFEITO!' ? '#ffd34d' : julg === 'ERROU' ? '#ff6b6b' : '#7df9ff'; ctx.fillText(julg, W/2, HIT_Y - 140 - (.6 - julgT)*40); ctx.globalAlpha = 1; }
  if (estado === 'jogando' && t < 0) { ctx.font = 'bold 64px system-ui'; ctx.textAlign = 'center'; ctx.fillStyle = '#fff'; ctx.fillText(Math.ceil(-t), W/2, H/2 - 40); }
  if (estado === 'jogando') { const prog = Math.max(0, Math.min(1, t/duracao)); ctx.fillStyle = 'rgba(255,255,255,.15)'; ctx.fillRect(12, 44, W - 24, 4); ctx.fillStyle = '#ffd34d'; ctx.fillRect(12, 44, (W - 24)*prog, 4);
    if (t > duracao) fim(); }
  $('hud').innerHTML = '<span>🎵 Música ' + musica + '</span><span>⭐ ' + pontos + '</span><span>' + (combo > 2 ? '🔥 ' + combo + ' (x' + (1 + Math.floor(combo/10)) + ')' : '') + '</span>';
}
function fim(){ estado = 'fim'; const total = notas.length || 1, prec = (acertos.p + acertos.o*.8 + acertos.b*.5)/total;
  const nota = prec > .95 ? 'S' : prec > .85 ? 'A' : prec > .7 ? 'B' : prec > .5 ? 'C' : 'D'; recorde = salvarRecorde('rec_sinfonia', pontos);
  acorde(nota === 'S' || nota === 'A' ? [523, 659, 784, 1046, 1318] : [392, 466, 523], .2);
  tela('<h1>🎼 Nota ' + nota + '</h1><p class="grande">⭐ ' + pontos + '</p><p>Precisão ' + Math.round(prec*100) + '% · combo máximo ' + maxCombo + '</p>' +
    '<p>✨ ' + acertos.p + ' perfeitos · 💙 ' + acertos.o + ' ótimos · 🙂 ' + acertos.b + ' bons · ❌ ' + acertos.e + ' erros</p><p>Você acendeu ' + estrelas.length + ' estrelas na sua constelação 🌌</p>' +
    (prec >= .6 ? '<button id="bj">🎵 Próxima música</button>' : '<button id="bj">🔁 Tentar de novo</button>'));
  $('bj').onclick = () => { if (prec >= .6) musica++; comecar(); }; }
let ult = performance.now(); function loop(){ desenhar(); requestAnimationFrame(loop); }
tela('<h1>🎹 Sinfonia das Estrelas</h1><p>Cada música é <b>composta na hora</b> só para você. Acerte as notas no tempo certo e <b>você mesmo toca a melodia</b>!</p>' +
     '<p>⌨️ Teclas <b>D F J K</b> · 📱 toque nas 4 faixas</p><p>Cada acerto perfeito acende uma estrela na sua constelação ✨</p><p>🔊 Ligue o som!</p><p>🏆 Recorde: ' + recorde + '</p><button id="bj">🎵 Tocar</button>');
$('bj').onclick = comecar; requestAnimationFrame(loop);
"""

# ---------------------------------------------------------------- JOIAS ENCANTADAS
JOIAS_JS = r"""
const W = 480, H = 600, cv = $('c'), ctx = cv.getContext('2d'); cv.width = W; cv.height = H;
const N = 8, T = 56, OX = (W - N*T)/2, OY = 110;
const CORES = [['#ff4d6d', '#a4133c'], ['#ffd60a', '#b08900'], ['#5be08a', '#157a3c'], ['#4fc3ff', '#0b4f8a'], ['#c77dff', '#5a189a'], ['#ff9f1c', '#a64b00']];
let grade, sel = null, anim = false, part = [], textos = [], pontos = 0, movs, meta, nivel = 1, estado = 'inicio', cascata = 0, ocioso = 0, dica = null, tremor = 0;
let recorde = lerRecorde('rec_joias');
function nova(tipo){ return {t: tipo ?? Math.floor(Math.random()*6), esp: null, dx: 0, dy: 0, esc: 1}; }
function gerar(){ grade = []; for (let r = 0; r < N; r++) { grade.push([]); for (let c = 0; c < N; c++) { let j; do { j = nova(); } while ((c >= 2 && grade[r][c-1].t === j.t && grade[r][c-2].t === j.t) || (r >= 2 && grade[r-1][c].t === j.t && grade[r-2][c].t === j.t)); grade[r].push(j); } }
  if (!temJogada()) gerar(); }
function comecarNivel(){ movs = Math.max(14, 24 - nivel); meta = 1500 + nivel*1200 + nivel*nivel*150; pontos = 0; gerar();
  for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) grade[r][c].dy = -(N - r)*T - 200 - c*20; anim = true; estado = 'jogando'; }
function achar(){ const marc = new Set(), grupos = [];
  for (let r = 0; r < N; r++) { let c = 0; while (c < N) { let k = c; while (k + 1 < N && grade[r][k+1] && grade[r][c] && grade[r][k+1].t === grade[r][c].t && grade[r][c].t >= 0) k++;
    if (k - c >= 2) { const g = []; for (let x = c; x <= k; x++) { g.push([r, x]); marc.add(r*N + x); } grupos.push({cel: g, dir: 'h'}); } c = k + 1; } }
  for (let c = 0; c < N; c++) { let r = 0; while (r < N) { let k = r; while (k + 1 < N && grade[k+1][c] && grade[r][c] && grade[k+1][c].t === grade[r][c].t && grade[r][c].t >= 0) k++;
    if (k - r >= 2) { const g = []; for (let y = r; y <= k; y++) { g.push([y, c]); marc.add(y*N + c); } grupos.push({cel: g, dir: 'v'}); } r = k + 1; } }
  return {marc, grupos}; }
function temJogada(){ for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) for (const [dr, dc] of [[0, 1], [1, 0]]) { const r2 = r + dr, c2 = c + dc; if (r2 >= N || c2 >= N) continue;
  trocaSimples(r, c, r2, c2); const ok = achar().marc.size > 0; trocaSimples(r, c, r2, c2); if (ok) { dica = [[r, c], [r2, c2]]; return true; } } return false; }
function trocaSimples(r, c, r2, c2){ const t = grade[r][c]; grade[r][c] = grade[r2][c2]; grade[r2][c2] = t; }
function explodirCel(r, c, cor, n = 12){ const x = OX + c*T + T/2, y = OY + r*T + T/2; for (let i = 0; i < n; i++) { const a = Math.random()*6.28, s = 60 + Math.random()*260; part.push({x, y, vx: Math.cos(a)*s, vy: Math.sin(a)*s - 80, t: .5 + Math.random()*.6, cor, r: 2 + Math.random()*3}); } }
function limpar(alvos){ let n = 0; const fila = [...alvos], visto = new Set();
  while (fila.length) { const k = fila.pop(); if (visto.has(k)) continue; visto.add(k); const r = Math.floor(k/N), c = k % N, j = grade[r][c]; if (!j) continue;
    if (j.esp === 'raio') { for (let x = 0; x < N; x++) fila.push(r*N + x); for (let y = 0; y < N; y++) fila.push(y*N + c); textos.push({txt: '⚡ RAIO!', x: OX + c*T + T/2, y: OY + r*T, t: 1}); tremor = .25; }
    if (j.esp === 'bomba') { for (let y = r - 1; y <= r + 1; y++) for (let x = c - 1; x <= c + 1; x++) if (y >= 0 && x >= 0 && y < N && x < N) fila.push(y*N + x); textos.push({txt: '💥 BOMBA!', x: OX + c*T + T/2, y: OY + r*T, t: 1}); tremor = .35; ruido(.3, .12); }
    explodirCel(r, c, j.t >= 0 ? CORES[j.t][0] : '#fff', j.esp ? 30 : 12); grade[r][c] = null; n++; }
  return n; }
function resolver(origem){
  const {marc, grupos} = achar(); if (!marc.size) { cascata = 0; anim = false; if (!temJogada()) { textos.push({txt: '🔀 Embaralhando…', x: W/2, y: H/2, t: 1.5}); gerar(); } verificarFim(); return; }
  cascata++; const especiais = [];
  for (const g of grupos) { if (g.cel.length >= 5) especiais.push({pos: escolherPos(g.cel, origem), esp: 'estrela', t: -1}); else if (g.cel.length === 4) especiais.push({pos: escolherPos(g.cel, origem), esp: 'raio', t: grade[g.cel[0][0]][g.cel[0][1]].t}); }
  const cont = {}; for (const k of marc) cont[k] = (cont[k] || 0) + 1;
  for (const g of grupos) for (const [r, c] of g.cel) if (grupos.filter(o => o.cel.some(([a, b]) => a === r && b === c)).length > 1 && !especiais.some(e => e.pos[0] === r && e.pos[1] === c))
    especiais.push({pos: [r, c], esp: 'bomba', t: grade[r][c].t});
  const n = limpar([...marc].filter(k => !especiais.some(e => e.pos[0]*N + e.pos[1] === k)));
  for (const e of especiais) { const [r, c] = e.pos; grade[r][c] = {t: e.t, esp: e.esp, dx: 0, dy: 0, esc: 1.6}; bip(1500, .2, 'sine', .06); }
  const ganho = n*20*cascata*(1 + Math.floor(nivel/3)); pontos += ganho;
  textos.push({txt: '+' + ganho + (cascata > 1 ? ' ×' + cascata : ''), x: OX + N*T/2, y: OY + N*T/2 - 20, t: 1});
  const notas = [523, 587, 659, 784, 880, 1046, 1175, 1318]; bip(notas[Math.min(cascata - 1, 7)], .18, 'triangle', .08); bip(notas[Math.min(cascata - 1, 7)]*1.5, .14, 'sine', .03);
  if (cascata >= 3) vibrar(40);
  setTimeout(cair, 170); }
function escolherPos(cel, origem){ if (origem) for (const o of origem) if (cel.some(([r, c]) => r === o[0] && c === o[1])) return o; return cel[Math.floor(cel.length/2)]; }
function cair(){ for (let c = 0; c < N; c++) { let vazio = 0; for (let r = N - 1; r >= 0; r--) { if (!grade[r][c]) vazio++; else if (vazio) { grade[r + vazio][c] = grade[r][c]; grade[r][c] = null; grade[r + vazio][c].dy -= vazio*T; } }
  for (let r = 0; r < vazio; r++) { const j = nova(); j.dy = -(vazio)*T - 30; grade[r][c] = j; } } setTimeout(() => resolver(null), 260); }
function trocar(a, b){ if (anim || estado !== 'jogando') return; const [r, c] = a, [r2, c2] = b; if (Math.abs(r - r2) + Math.abs(c - c2) !== 1) return;
  anim = true; ocioso = 0; dica = null; const ja = grade[r][c], jb = grade[r2][c2];
  trocaSimples(r, c, r2, c2); ja.dx += (c - c2)*T; ja.dy += (r - r2)*T; jb.dx += (c2 - c)*T; jb.dy += (r2 - r)*T; bip(660, .05, 'sine', .04);
  if (ja.esp === 'estrela' || jb.esp === 'estrela') { const cor = ja.esp === 'estrela' ? jb.t : ja.t; movs--; const alvos = [];
    for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) if (grade[y][x] && (grade[y][x].t === cor || grade[y][x].esp === 'estrela')) alvos.push(y*N + x);
    setTimeout(() => { textos.push({txt: '🌟 ESTRELA!', x: W/2, y: OY + 40, t: 1.4}); tremor = .4; acorde([784, 988, 1175, 1568], .1); const n = limpar(alvos); pontos += n*60; cascata = 1; setTimeout(cair, 220); }, 160); return; }
  setTimeout(() => { if (achar().marc.size) { movs--; resolver([[r, c], [r2, c2]]); }
    else { trocaSimples(r, c, r2, c2); ja.dx += (c2 - c)*T; ja.dy += (r2 - r)*T; jb.dx += (c - c2)*T; jb.dy += (r - r2)*T; bip(200, .1, 'sawtooth', .04); setTimeout(() => anim = false, 180); } }, 170); }
function verificarFim(){ if (pontos >= meta) { estado = 'venceu'; recorde = salvarRecorde('rec_joias', nivel + 1); acorde([523, 659, 784, 1046, 1318], .15);
    for (let i = 0; i < 6; i++) setTimeout(() => { const r = Math.floor(Math.random()*N), c = Math.floor(Math.random()*N); explodirCel(r, c, CORES[i % 6][0], 40); }, i*120);
    setTimeout(() => { tela('<h1>💎 Nível ' + nivel + ' completo!</h1><p class="grande">⭐ ' + pontos + '</p><p>Sobraram ' + movs + ' jogadas</p><button id="bj">✨ Próximo nível</button>'); $('bj').onclick = () => { nivel++; tela(null); comecarNivel(); }; }, 900); }
  else if (movs <= 0) { estado = 'fim'; setTimeout(() => { tela('<h1>💔 Acabaram as jogadas</h1><p class="grande">' + pontos + ' / ' + meta + '</p><p>Nível ' + nivel + '</p><button id="bj">🔁 Tentar de novo</button>'); $('bj').onclick = () => { tela(null); comecarNivel(); }; }, 500); } }
function celula(e){ const r = cv.getBoundingClientRect(), x = (e.clientX - r.left)/r.width*W, y = (e.clientY - r.top)/r.height*H; const c = Math.floor((x - OX)/T), rr = Math.floor((y - OY)/T);
  return rr >= 0 && rr < N && c >= 0 && c < N ? [rr, c] : null; }
let ini = null;
cv.addEventListener('pointerdown', e => { audio(); const p = celula(e); if (!p) return; cv.setPointerCapture(e.pointerId); ini = {p, x: e.clientX, y: e.clientY};
  if (sel && Math.abs(sel[0] - p[0]) + Math.abs(sel[1] - p[1]) === 1) { trocar(sel, p); sel = null; ini = null; } else sel = p; });
cv.addEventListener('pointermove', e => { if (!ini) return; const dx = e.clientX - ini.x, dy = e.clientY - ini.y, lim = cv.getBoundingClientRect().width/N*.35;
  if (Math.hypot(dx, dy) > lim) { const [r, c] = ini.p; const alvo = Math.abs(dx) > Math.abs(dy) ? [r, c + Math.sign(dx)] : [r + Math.sign(dy), c];
    if (alvo[0] >= 0 && alvo[0] < N && alvo[1] >= 0 && alvo[1] < N) trocar(ini.p, alvo); sel = null; ini = null; } });
['pointerup', 'pointercancel'].forEach(t => cv.addEventListener(t, () => ini = null));
function desenharJoia(j, x, y, s, tempo){ if (!j) return; const r = T*.38*s;
  ctx.save(); ctx.translate(x, y);
  if (j.esp === 'estrela') { ctx.rotate(tempo*1.5); const g = ctx.createRadialGradient(0, 0, 2, 0, 0, r*1.2); g.addColorStop(0, '#fff');
    ['#ff4d6d', '#ffd60a', '#5be08a', '#4fc3ff', '#c77dff'].forEach((c, i) => g.addColorStop(.25 + i*.15, c));
    ctx.shadowColor = '#fff'; ctx.shadowBlur = 20; ctx.fillStyle = g; ctx.beginPath(); for (let i = 0; i < 10; i++) { const a = i*Math.PI/5, rr = i % 2 ? r*.5 : r*1.1; ctx.lineTo(Math.cos(a)*rr, Math.sin(a)*rr); } ctx.fill(); ctx.restore(); return; }
  const [c1, c2] = CORES[j.t]; const g = ctx.createRadialGradient(-r*.35, -r*.35, r*.1, 0, 0, r*1.1); g.addColorStop(0, '#fff'); g.addColorStop(.25, c1); g.addColorStop(1, c2);
  ctx.fillStyle = g; ctx.shadowColor = c1; ctx.shadowBlur = j.esp ? 22 : 8; ctx.beginPath();
  const lados = [0, 4, 6, 3, 5, 8][j.t];
  if (!lados) ctx.arc(0, 0, r, 0, 7); else for (let i = 0; i < lados; i++) { const a = i*2*Math.PI/lados - Math.PI/2 + (j.t === 1 ? Math.PI/4 : 0); ctx.lineTo(Math.cos(a)*r*(j.t === 1 ? 1.05 : 1), Math.sin(a)*r*(j.t === 1 ? 1.05 : 1)); }
  ctx.closePath(); ctx.fill(); ctx.shadowBlur = 0;
  ctx.fillStyle = 'rgba(255,255,255,.45)'; ctx.beginPath(); ctx.ellipse(-r*.25, -r*.35, r*.35, r*.16, -.5, 0, 7); ctx.fill();
  if (j.esp === 'raio') { ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(-r*.2, -r*.6); ctx.lineTo(r*.1, -r*.05); ctx.lineTo(-r*.1, r*.05); ctx.lineTo(r*.2, r*.6); ctx.stroke(); }
  if (j.esp === 'bomba') { ctx.strokeStyle = `rgba(255,255,255,${.5 + Math.sin(tempo*8)*.4})`; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(0, 0, r*.55, 0, 7); ctx.stroke(); }
  ctx.restore(); }
let ult = performance.now(), relogio = 0;
function loop(t){ const dt = Math.min(.033, (t - ult)/1000); ult = t; relogio += dt; requestAnimationFrame(loop);
  if (grade) for (const l of grade) for (const j of l) if (j) { j.dx *= Math.pow(.0005, dt); j.dy = j.dy < 0 ? Math.min(0, j.dy + 900*dt) : j.dy*Math.pow(.0005, dt); if (Math.abs(j.dx) < .5) j.dx = 0; j.esc += (1 - j.esc)*Math.min(1, dt*6); }
  if (anim && grade && estado === 'jogando' && grade.flat().every(j => !j || (Math.abs(j.dx) < 1 && Math.abs(j.dy) < 1)) && cascata === 0 && !sel) { }
  if (estado === 'jogando' && !anim) ocioso += dt;
  for (const p of part) { p.x += p.vx*dt; p.y += p.vy*dt; p.vy += 500*dt; p.t -= dt; } part = part.filter(p => p.t > 0);
  for (const x of textos) { x.t -= dt; x.y -= 30*dt; } textos = textos.filter(x => x.t > 0); tremor = Math.max(0, tremor - dt);
  if (anim && cascata === 0 && grade && grade.flat().every(j => j && Math.abs(j.dy) < 1 && Math.abs(j.dx) < 1) && estado === 'jogando') { const {marc} = achar(); if (marc.size) resolver(null); else anim = false; }
  // desenho
  const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#1a0b3b'); g.addColorStop(1, '#0a1630'); ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 40; i++) { ctx.globalAlpha = .3 + .3*Math.sin(relogio*2 + i); ctx.fillStyle = '#fff'; ctx.fillRect((i*131) % W, (i*71) % H, 1.5, 1.5); } ctx.globalAlpha = 1;
  ctx.save(); if (tremor) ctx.translate((Math.random() - .5)*tremor*20, (Math.random() - .5)*tremor*20);
  ctx.fillStyle = 'rgba(255,255,255,.06)'; ctx.fillRect(OX - 6, OY - 6, N*T + 12, N*T + 12);
  for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) { ctx.fillStyle = (r + c) % 2 ? 'rgba(255,255,255,.05)' : 'rgba(255,255,255,.09)'; ctx.fillRect(OX + c*T, OY + r*T, T, T); }
  if (sel) { ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.strokeRect(OX + sel[1]*T + 3, OY + sel[0]*T + 3, T - 6, T - 6); ctx.lineWidth = 1; }
  ctx.save(); ctx.beginPath(); ctx.rect(OX, OY, N*T, N*T); ctx.clip();
  if (grade) for (let r = 0; r < N; r++) for (let c = 0; c < N; c++) { const j = grade[r][c]; if (!j) continue;
    let s = j.esc; if (dica && ocioso > 5 && dica.some(([a, b]) => a === r && b === c)) s *= 1 + Math.sin(relogio*8)*.1;
    if (sel && sel[0] === r && sel[1] === c) s *= 1.1 + Math.sin(relogio*10)*.04;
    desenharJoia(j, OX + c*T + T/2 + j.dx, OY + r*T + T/2 + j.dy, s, relogio); }
  ctx.restore();
  for (const p of part) { ctx.globalAlpha = Math.min(1, p.t*2); ctx.fillStyle = p.cor; ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, 7); ctx.fill(); } ctx.globalAlpha = 1;
  ctx.restore();
  for (const x of textos) { ctx.globalAlpha = Math.min(1, x.t*2); ctx.font = 'bold 26px system-ui'; ctx.textAlign = 'center'; ctx.fillStyle = '#ffd34d'; ctx.strokeStyle = '#000'; ctx.lineWidth = 4;
    ctx.strokeText(x.txt, x.x, x.y); ctx.fillText(x.txt, x.x, x.y); } ctx.globalAlpha = 1; ctx.lineWidth = 1;
  if (meta) { const p = Math.min(1, pontos/meta); ctx.fillStyle = 'rgba(255,255,255,.12)'; rr(OX, 70, N*T, 16, 8); ctx.fill();
    const gp = ctx.createLinearGradient(OX, 0, OX + N*T, 0); gp.addColorStop(0, '#c77dff'); gp.addColorStop(1, '#ffd60a'); ctx.fillStyle = gp; rr(OX, 70, Math.max(16, N*T*p), 16, 8); ctx.fill();
    ctx.font = 'bold 12px system-ui'; ctx.textAlign = 'center'; ctx.fillStyle = '#fff'; ctx.fillText(pontos + ' / ' + meta, W/2, 82); }
  $('hud').innerHTML = '<span>💎 Nível ' + nivel + '</span><span>👆 ' + (movs ?? '-') + ' jogadas</span><span>🏆 ' + Math.max(1, recorde) + '</span>';
}
function rr(x, y, w, h, r){ ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r); ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath(); }
addEventListener('keydown', e => { if ((e.code === 'Space' || e.code === 'Enter') && estado !== 'jogando') { e.preventDefault(); const b = $('bj'); if (b) b.click(); } });
gerar();
tela('<h1>💎 Joias Encantadas</h1><p>Troque joias vizinhas para alinhar <b>3 ou mais iguais</b>. Bata a meta de pontos antes de acabarem as jogadas!</p>' +
     '<p>⚡ 4 em linha = <b>Raio</b> (limpa linha e coluna) · 💥 em L ou T = <b>Bomba</b> · 🌟 5 em linha = <b>Estrela</b> (troque com uma cor para apagar todas dela)</p>' +
     '<p>👆 Arraste uma joia ou toque em duas vizinhas</p><p>🏆 Chegou ao nível ' + Math.max(1, recorde) + '</p><button id="bj">✨ Jogar</button>');
$('bj').onclick = () => { tela(null); audio(); comecarNivel(); }; requestAnimationFrame(loop);
"""

# ---------------------------------------------------------------- VOO ALIENÍGENA (raymarching)
VOO_JS = r"""
const W = 480, H = 640, cv = $('c'), ov = $('ov'), oc = ov.getContext('2d');
ov.width = W; ov.height = H;
const gl = cv.getContext('webgl', {antialias: false}) || cv.getContext('experimental-webgl');
if (!gl) { tela('<h1>😕 Sem WebGL</h1><p>Seu navegador não suporta WebGL, necessário para este mundo.</p>'); throw new Error('sem webgl'); }
let escala = .6; function dimensionar(){ cv.width = Math.round(W*escala); cv.height = Math.round(H*escala); gl.viewport(0, 0, cv.width, cv.height); } dimensionar();
const FRAG = `precision highp float;
uniform vec2 res; uniform vec3 cam; uniform float yaw, pitch, roll, tempo;
float hash(vec2 p){ vec3 p3 = fract(vec3(p.xyx)*.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y)*p3.z); }
float noise(vec2 p){ vec2 i = floor(p), f = fract(p); vec2 u = f*f*(3. - 2.*f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), u.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), u.x), u.y); }
float fbm(vec2 p){ float v = 0., a = .5; for (int i = 0; i < 5; i++) { v += a*noise(p); p *= 2.03; a *= .5; } return v; }
float caminho(float z){ return sin(z*.013)*28. + sin(z*.0047)*45.; }
float altura(vec2 p){ float d = abs(p.x - caminho(p.y)); float vale = smoothstep(5., 30., d); return fbm(p*.045)*16. + vale*vale*42. - 6.; }
vec3 ceu(vec3 rd){ vec3 c = mix(vec3(.55, .25, .65), vec3(.05, .02, .18), clamp(rd.y*2.2, 0., 1.));
  vec3 sd = normalize(vec3(-.4, .25, -1.)); float s = max(dot(rd, sd), 0.);
  c += vec3(1., .45, .7)*pow(s, 300.)*3. + vec3(1., .3, .5)*pow(s, 8.)*.35;
  vec3 ld = normalize(vec3(.6, .45, -1.)); float l = max(dot(rd, ld), 0.); c += vec3(.6, 1., .9)*smoothstep(.9985, .999, l);
  float est = step(.996, hash(floor(rd.xy*400.))); c += est*vec3(1.)*clamp(rd.y*3., 0., 1.); return c; }
void main(){
  vec2 uv = (gl_FragCoord.xy - .5*res)/res.y;
  vec3 fw = normalize(vec3(sin(yaw), pitch, -cos(yaw))); vec3 rt = normalize(cross(fw, vec3(0, 1, 0))); vec3 up = cross(rt, fw);
  float cr = cos(roll), sr = sin(roll); vec3 r2 = rt*cr + up*sr, u2 = up*cr - rt*sr;
  vec3 rd = normalize(fw*1.3 + uv.x*r2 + uv.y*u2), ro = cam;
  float t = .5, hit = -1.;
  for (int i = 0; i < 100; i++) { vec3 p = ro + rd*t; float h = p.y - altura(p.xz); if (h < .015*t) { hit = t; break; } t += max(.1, h*.5); if (t > 280.) break; }
  vec3 col = ceu(rd);
  if (hit > 0.) { vec3 p = ro + rd*hit; vec2 e = vec2(.15, 0.);
    vec3 n = normalize(vec3(altura(p.xz - e.xy) - altura(p.xz + e.xy), 2.*e.x, altura(p.xz - e.yx) - altura(p.xz + e.yx)));
    float f = fbm(p.xz*.08); vec3 base = mix(vec3(.28, .12, .38), vec3(.12, .35, .42), smoothstep(.3, .7, f));
    base = mix(base, vec3(.85, .8, .95), smoothstep(18., 30., p.y)*smoothstep(.3, .8, n.y));
    vec3 sd = normalize(vec3(-.4, .5, -1.)); float dif = max(dot(n, sd), 0.);
    col = base*(.25 + .9*dif) + vec3(.4, .2, .5)*(1. - n.y)*.15;
    float cristal = smoothstep(.74, .78, fbm(p.xz*.35 + 7.));
    col += cristal*vec3(.2, 1., .9)*(1.2 + .5*sin(tempo*3. + p.x));
    float fog = 1. - exp(-hit*hit*.00004 - hit*.004); col = mix(col, vec3(.45, .22, .55), fog); }
  col = pow(col, vec3(.85)); col *= 1. - .25*dot(uv, uv);
  gl_FragColor = vec4(col, 1.); }`;
function compilar(tipo, src){ const s = gl.createShader(tipo); gl.shaderSource(s, src); gl.compileShader(s);
  if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s)); return s; }
const prog = gl.createProgram();
gl.attachShader(prog, compilar(gl.VERTEX_SHADER, 'attribute vec2 a; void main(){ gl_Position = vec4(a, 0., 1.); }'));
gl.attachShader(prog, compilar(gl.FRAGMENT_SHADER, FRAG)); gl.linkProgram(prog); gl.useProgram(prog);
const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW);
const loc = gl.getAttribLocation(prog, 'a'); gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, 2, gl.FLOAT, false, 0, 0);
const U = {}; ['res', 'cam', 'yaw', 'pitch', 'roll', 'tempo'].forEach(n => U[n] = gl.getUniformLocation(prog, n));
// mesma matemática no JavaScript (para colisão)
const fract = x => x - Math.floor(x);
function hash(x, y){ let a = fract(x*.1031), b = fract(y*.1031), c = fract(x*.1031); const d = a*(b + 33.33) + b*(c + 33.33) + c*(a + 33.33); a += d; b += d; c += d; return fract((a + b)*c); }
function noise(x, y){ const ix = Math.floor(x), iy = Math.floor(y), fx = x - ix, fy = y - iy, ux = fx*fx*(3 - 2*fx), uy = fy*fy*(3 - 2*fy);
  const a = hash(ix, iy), b = hash(ix + 1, iy), c = hash(ix, iy + 1), d = hash(ix + 1, iy + 1); return (a + (b - a)*ux)*(1 - uy) + (c + (d - c)*ux)*uy; }
function fbm(x, y){ let v = 0, a = .5; for (let i = 0; i < 5; i++) { v += a*noise(x, y); x *= 2.03; y *= 2.03; a *= .5; } return v; }
const caminho = z => Math.sin(z*.013)*28 + Math.sin(z*.0047)*45;
function altura(x, z){ const d = Math.abs(x - caminho(z)); const t = Math.max(0, Math.min(1, (d - 5)/25)), v = t*t*(3 - 2*t); return fbm(x*.045, z*.045)*16 + v*v*42 - 6; }
let bonus = 0, estado = 'inicio', p = {x: 0, y: 8, z: 0}, vx = 0, vy = 0, yaw = 0, roll = 0, vel = 28, dist = 0, pontos = 0, aneis = [], proxAnel = 80, energia = 3, invul = 0, combo = 0, tempoJogo = 0, tremor = 0;
let recorde = lerRecorde('rec_voo'), teclas = {}, alvoMouse = null, fpsMed = 60;
const ALT_MAX = 30;
function comecar(){ p = {x: caminho(0), y: altura(caminho(0), 0) + 13, z: 0}; vx = vy = 0; vel = 28; dist = 0; pontos = 0; aneis = []; proxAnel = 80; energia = 3; invul = 2; combo = 0; tempoJogo = 0; bonus = 0;
  estado = 'jogando'; tela(null); audio(); cv.focus(); }
function criarAnel(z){ const cx = caminho(-z); aneis.push({x: cx + (Math.random() - .5)*14, z: z, y: 0, ok: false}); const a = aneis[aneis.length - 1]; a.y = Math.max(altura(a.x, -z) + 6, altura(cx, -z) + 7 + Math.random()*6); }
addEventListener('keydown', e => { teclas[e.code] = true; if (e.code.startsWith('Arrow') || e.code === 'Space') e.preventDefault();
  if ((e.code === 'Space' || e.code === 'Enter') && estado !== 'jogando') { const b = $('bj'); if (b) b.click(); } });
addEventListener('keyup', e => teclas[e.code] = false);
ov.addEventListener('pointerdown', e => { ov.setPointerCapture(e.pointerId); mira(e); }); ov.addEventListener('pointermove', e => { if (e.buttons || e.pointerType === 'mouse') mira(e); });
['pointerup', 'pointercancel'].forEach(t => ov.addEventListener(t, e => { if (e.pointerType !== 'mouse') alvoMouse = null; }));
ov.addEventListener('pointerleave', () => alvoMouse = null);
function mira(e){ const r = ov.getBoundingClientRect(); alvoMouse = {x: ((e.clientX - r.left)/r.width - .5)*2, y: -((e.clientY - r.top)/r.height - .5)*2}; }
function norm(v){ const m = Math.hypot(...v); return v.map(x => x/m); }
function cruz(a, b){ return [a[1]*b[2] - a[2]*b[1], a[2]*b[0] - a[0]*b[2], a[0]*b[1] - a[1]*b[0]]; }
let pit = -.15;
function projetar(x, y, z){ const fw = norm([Math.sin(yaw), pit, -Math.cos(yaw)]), rt = norm(cruz(fw, [0, 1, 0])), up = cruz(rt, fw);
  const cr = Math.cos(roll), sr = Math.sin(roll), r2 = rt.map((v, i) => v*cr + up[i]*sr), u2 = up.map((v, i) => v*cr - rt[i]*sr);
  const d = [x - p.x, y - p.y, z - p.z], zf = d[0]*fw[0] + d[1]*fw[1] + d[2]*fw[2]; if (zf < .5) return null;
  const sx = (d[0]*r2[0] + d[1]*r2[1] + d[2]*r2[2])/zf*1.3, sy = (d[0]*u2[0] + d[1]*u2[1] + d[2]*u2[2])/zf*1.3;
  return {x: W/2 + sx*H, y: H/2 - sy*H, esc: H*1.3/zf}; }
let ult = performance.now(), relogio = 0;
function loop(t){ const dt = Math.min(.05, (t - ult)/1000); ult = t; relogio += dt; requestAnimationFrame(loop);
  fpsMed = fpsMed*.95 + (1/Math.max(dt, .001))*.05;
  if (relogio > 3 && Math.floor(relogio*2) % 6 === 0) { if (fpsMed < 28 && escala > .35) { escala -= .05; dimensionar(); fpsMed = 45; } else if (fpsMed > 57 && escala < .8) { escala += .05; dimensionar(); fpsMed = 45; } }
  if (estado === 'jogando') {
    tempoJogo += dt; vel = Math.min(70, 28 + tempoJogo*.6);
    let ix = (teclas.ArrowRight || teclas.KeyD ? 1 : 0) - (teclas.ArrowLeft || teclas.KeyA ? 1 : 0), iy = (teclas.ArrowUp || teclas.KeyW ? 1 : 0) - (teclas.ArrowDown || teclas.KeyS ? 1 : 0);
    if (alvoMouse) { ix = Math.max(-1, Math.min(1, alvoMouse.x*1.6)); iy = Math.max(-1, Math.min(1, alvoMouse.y*1.6)); }
    vx += (ix*26 - vx)*Math.min(1, dt*3); vy += (iy*14 - vy)*Math.min(1, dt*3);
    const curva = (caminho(p.z - vel*.25) - caminho(p.z))/(vel*.25)*vel;  // o cânion faz curva: um leve piloto automático ajuda
    p.x += (vx + curva*.75)*dt; p.y = Math.min(ALT_MAX, p.y + vy*dt); p.z -= vel*dt; dist += vel*dt; pontos = Math.floor(dist/2) + bonus;
    yaw = Math.atan2(vx + curva*.75, vel)*.9; roll += (-vx*.025 - roll)*Math.min(1, dt*4);
    invul = Math.max(0, invul - dt);
    const chao = altura(p.x, p.z);
    if (p.y - chao < 5) p.y += (5 - (p.y - chao))*1.6*dt;  // sensor de proximidade do solo
    if (p.y < chao + 1.4 && invul <= 0) { energia--; invul = 1.8; tremor = .6; combo = 0; ruido(.5, .22); vibrar(200); p.y = chao + 6; vy = 8;
      if (energia <= 0) { estado = 'fim'; recorde = salvarRecorde('rec_voo', pontos);
        tela('<h1>💥 Pouso forçado!</h1><p class="grande">🛸 ' + pontos + ' pts · ' + Math.floor(dist) + ' m</p><p>🏆 Recorde: ' + recorde + '</p><button id="bj">🛸 Voar de novo</button>'); $('bj').onclick = comecar; } }
    else if (p.y < chao + 1.4) p.y = chao + 1.4;
    proxAnel -= vel*dt; if (proxAnel <= 0) { criarAnel(-(p.z - 260)); proxAnel = 70 + Math.random()*40; }
    for (const a of aneis) if (!a.ok && -a.z >= p.z && -a.z < p.z + vel*dt + 1) { a.ok = true;
      if (Math.hypot(a.x - p.x, a.y - p.y) < 5) { combo++; bonus += 250*combo; vel += 3; const f = [523, 659, 784, 1046, 1318][Math.min(combo - 1, 4)]; bip(f, .3, 'sine', .08); bip(f*1.5, .2, 'triangle', .03); }
      else { combo = 0; bip(200, .15, 'triangle', .04); } }
    aneis = aneis.filter(a => -a.z < p.z + 5);
  } else { p.z -= 18*dt; p.x += (caminho(p.z) - p.x)*Math.min(1, dt*2); p.y += (altura(caminho(p.z), p.z) + 10 - p.y)*Math.min(1, dt*2);
    yaw = Math.atan2(caminho(p.z - 20) - p.x, 20)*.6; roll = Math.sin(relogio*.5)*.1; }
  tremor = Math.max(0, tremor - dt);
  gl.uniform2f(U.res, cv.width, cv.height); gl.uniform3f(U.cam, p.x + (Math.random() - .5)*tremor, p.y + (Math.random() - .5)*tremor, p.z);
  gl.uniform1f(U.yaw, yaw); pit = estado === 'jogando' ? -.12 + vy*.008 : -.15; gl.uniform1f(U.pitch, pit); gl.uniform1f(U.roll, roll); gl.uniform1f(U.tempo, relogio);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
  // sobreposição: anéis, nave e painel
  oc.clearRect(0, 0, W, H);
  for (const a of aneis) { if (a.ok) continue; const s = projetar(a.x, a.y, -a.z); if (!s) continue; const r = 5*s.esc;
    if (r > 900) continue; oc.strokeStyle = 'rgba(125,249,255,.9)'; oc.lineWidth = Math.max(2, r*.08); oc.shadowColor = '#7df9ff'; oc.shadowBlur = 16;
    oc.beginPath(); oc.arc(s.x, s.y, r, 0, 7); oc.stroke(); oc.shadowBlur = 0; }
  if (estado === 'jogando' && (invul <= 0 || Math.floor(invul*10) % 2 === 0)) { oc.save(); oc.translate(W/2, H*.72); oc.rotate(-roll*1.4);
    oc.fillStyle = '#e8f7ff'; oc.beginPath(); oc.moveTo(0, -18); oc.lineTo(46, 10); oc.lineTo(12, 6); oc.lineTo(0, 16); oc.lineTo(-12, 6); oc.lineTo(-46, 10); oc.closePath(); oc.fill();
    oc.fillStyle = '#7df9ff'; oc.beginPath(); oc.ellipse(0, -2, 7, 9, 0, 0, 7); oc.fill();
    oc.shadowColor = '#ff5ea8'; oc.shadowBlur = 20; oc.fillStyle = '#ff9fd0'; oc.beginPath(); oc.arc(-9, 14, 3 + Math.random()*2, 0, 7); oc.arc(9, 14, 3 + Math.random()*2, 0, 7); oc.fill(); oc.restore(); }
  if (estado === 'jogando') { const alt = p.y - altura(p.x, p.z), perigo = alt < 5; oc.fillStyle = perigo ? 'rgba(255,80,80,.9)' : 'rgba(255,255,255,.7)';
    oc.font = 'bold 13px system-ui'; oc.textAlign = 'left'; oc.fillText('ALT ' + alt.toFixed(0) + (perigo ? ' ⚠️ SUBA!' : ''), 12, H - 16);
    if (p.y >= ALT_MAX - .5) { oc.fillStyle = 'rgba(255,211,77,.9)'; oc.fillText('Teto de voo: atmosfera rarefeita', 12, H - 34); } }
  $('hud').innerHTML = '<span>🛸 ' + pontos + '</span><span>' + (combo > 1 ? '💫 x' + combo : Math.floor(vel*3.6) + ' km/h') + '</span><span>' + '💜'.repeat(Math.max(0, energia)) + '</span>';
}
tela('<h1>🏔️ Voo Alienígena</h1><p>Um planeta inteiro <b>calculado pixel a pixel</b> em tempo real (raymarching). Voe pelo cânion sinuoso sem bater nas montanhas!</p>' +
     '<p>💫 Passe por dentro dos <b>anéis azuis</b> para combos e mais velocidade</p><p>🖱️ Mouse/dedo pilota · ⌨️ setas</p><p>🏆 Recorde: ' + recorde + '</p><button id="bj">🛸 Decolar</button>');
$('bj').onclick = comecar; requestAnimationFrame(loop);
"""

MUNDO = {
    "portal": (480, 700, PORTAL_JS, True, ""),
    "estilingue": (480, 700, ESTILINGUE_JS, False, ""),
    "sinfonia": (480, 760, SINFONIA_JS, False,
                 '<button data-l="0" style="background:#ff5ea8">D</button><button data-l="1" style="background:#c9a000">F</button>'
                 '<button data-l="2" style="background:#2e9c5a">J</button><button data-l="3" style="background:#2a8fb0">K</button>'),
    "joias": (480, 660, JOIAS_JS, False, ""),
    "voo": (480, 700, VOO_JS, False, ""),
}
SINFONIA_BOTOES_JS = r"""
document.querySelectorAll('[data-l]').forEach(b => b.addEventListener('pointerdown', e => { e.preventDefault(); bater(+b.dataset.l); }));
"""


def jogo_mundo(nome):
    largura, altura, js, tres_d, botoes = MUNDO[nome]
    extra = TELA_DIV
    if nome == "voo":
        extra = ("<canvas id='ov' style='position:absolute;inset:0;width:100%;height:100%;touch-action:none'></canvas>"
                 + TELA_DIV)
    if nome == "sinfonia":
        js = js + SINFONIA_BOTOES_JS
    pagina = pagina_tech(largura, extra, js, botoes, tres_d)
    if nome == "voo":  # o canvas WebGL tem resolução menor e é esticado; mantém proporção
        pagina = pagina.replace(".jogo canvas{width:100%;height:auto;", ".jogo canvas{width:100%;aspect-ratio:3/4;height:auto;")
    jogo_html(pagina, altura)
    st.caption("🖱️ No computador, clique no jogo antes de usar o teclado. 🔊 Ligue o som para a experiência completa."
               + (" 🌐 Precisa de internet para carregar o motor 3D." if tres_d else ""))


# =====================================================================
# ⚽ COPA DE FUTSAL (visto de cima, 6 x 6, torneio contra a IA)
# =====================================================================
FUTSAL_JS = r"""
const W = 520, H = 780, cv = $('c'), ctx = cv.getContext('2d'); cv.width = W; cv.height = H;
const CX = 30, CY = 62, CW = 460, CH = 690, MEIO = CX + CW/2, CENTRO = CY + CH/2, TOPO = CY, BASE = CY + CH, GOL = 110;
const FASES = [
  {nome: 'Oitavas de final', adv: 'Tatus de Cuiabá', cor: '#e53935', f: .78, roubo: .55, erro: .34, gk: 480, pensa: .6},
  {nome: 'Quartas de final', adv: 'Lobos do Cerrado', cor: '#8e24aa', f: .84, roubo: .7, erro: .27, gk: 520, pensa: .48},
  {nome: 'Semifinal', adv: 'Tubarões do Litoral', cor: '#00897b', f: .94, roubo: .9, erro: .19, gk: 610, pensa: .38},
  {nome: 'Final', adv: 'Dragões da Serra', cor: '#263238', f: 1.08, roubo: 1.3, erro: .1, gk: 800, pensa: .26}];
// Esquema tático 1-3-1 → número: [x, y na defesa, y no ataque, folga lateral, sigla, nome]
const PAPEIS = {1: [.5, .975, .975, 0, 'GOL', 'Goleiro'], 2: [.5, .80, .58, .16, 'FIX', 'Fixo'], 3: [.15, .70, .36, .11, 'ALA', 'Ala esquerda'],
  4: [.85, .70, .36, .11, 'ALA', 'Ala direita'], 5: [.5, .65, .45, .2, 'MEI', 'Meia'], 6: [.5, .54, .19, .22, 'PIV', 'Pivô']};
const FORM = [1, 2, 3, 4, 5, 6].map(n => [PAPEIS[n][0], PAPEIS[n][1]]);
const faseT = [.5, .5];
const ANDA = 66, CORRE = 118;
let fase = 0, jog = [], bola, estado = 'inicio', placar = [0, 0], relogio = 180, sel = 4, autoTroca = true, ouro = false, timer = 0, msg = '', msgT = 0;
let saidaPendente = false, saidaT = 0, carga = 0, tEspaco = 0, part = [], tremor = 0, saidaTime = 0, campanha = [];
const teclas = {};
function F(){ return FASES[fase]; }
function posForm(fx, fy, t){ return t === 0 ? [CX + fx*CW, CY + fy*CH] : [CX + (1 - fx)*CW, CY + (1 - fy)*CH]; }
function criarTimes(){ jog = [];
  for (let t = 0; t < 2; t++) FORM.forEach((f, i) => { const [x, y] = posForm(f[0], f[1], t);
    jog.push({t, n: i + 1, x, y, hx: f[0], hy: f[1], ang: t === 0 ? -Math.PI/2 : Math.PI/2, vx: 0, vy: 0, gk: i === 0, cd: 0, pensa: Math.random(), segura: 0, jx: 0, jy: 0, jt: 0}); }); }
function meu(n){ return jog.find(p => p.t === 0 && p.n === n); }
function saida(time){ jog.forEach(p => { const [x, y] = posForm(p.hx, Math.max(p.hy, .56), p.t); p.x = x; p.y = y; p.vx = p.vy = 0; p.ang = p.t === 0 ? -Math.PI/2 : Math.PI/2; p.cd = 0; });
  const k = jog.find(p => p.t === time && p.n === 6), m = jog.find(p => p.t === time && p.n === 5);
  k.x = MEIO; k.y = CENTRO + (time === 0 ? 16 : -16); m.x = MEIO - 40; m.y = CENTRO + (time === 0 ? 40 : -40);
  faseT[time] = .6; faseT[1 - time] = .3;
  bola = {x: MEIO, y: CENTRO, vx: 0, vy: 0, dono: k, giro: 0, ultimo: k}; if (time === 0) sel = 6; apito();
  saidaPendente = true; saidaT = 1.3; jog.forEach(q => { q.fica = 0; q.pensa = 0; });
  if (time === 0) aviso('Sua saída: gire com ← → e passe com ↑', 2.6); }
function novaPartida(){ criarTimes(); placar = [0, 0]; relogio = 180; ouro = false; part = []; saida(0); estado = 'jogando'; tela(null); audio(); cv.focus();
  aviso(F().nome + ': você x ' + F().adv, 2.2); }
function aviso(t, s = 1.6){ msg = t; msgT = s; }
function apito(){ bip(2200, .12, 'sine', .05); setTimeout(() => bip(2200, .3, 'sine', .05), 160); }
function chute(p, forca, ang){ p.fica = 1.8; bola.dono = null; bola.vx = Math.cos(ang)*forca; bola.vy = Math.sin(ang)*forca; bola.ultimo = p; p.cd = .3;
  bola.x = p.x + Math.cos(ang)*15; bola.y = p.y + Math.sin(ang)*15; ruido(.08, .12 + forca/9000); bip(120, .06, 'sine', .08); }
function angPara(a, b){ return Math.atan2(b.y - a.y, b.x - a.x); }
function difAng(a, b){ let d = b - a; while (d > Math.PI) d -= 2*Math.PI; while (d < -Math.PI) d += 2*Math.PI; return d; }
function girarPara(p, alvo, vel, dt){ const d = difAng(p.ang, alvo); p.ang += Math.max(-vel*dt, Math.min(vel*dt, d)); }
function mover(p, tx, ty, vel, dt){ const dx = tx - p.x, dy = ty - p.y, d = Math.hypot(dx, dy);
  if (d < 4) { p.vx *= .8; p.vy *= .8; return; } const v = Math.min(vel, d*4); p.vx = dx/d*v; p.vy = dy/d*v; girarPara(p, Math.atan2(dy, dx), 7, dt); }
function maisPerto(lista, x, y){ let m = null, md = 1e9; for (const p of lista) { const d = Math.hypot(p.x - x, p.y - y); if (d < md) { md = d; m = p; } } return [m, md]; }
// ---------- passes e chutes do jogador humano
function soltarPasse(forte){
  const p = meu(sel); if (!p || estado !== 'jogando') return; const c = Math.min(1, carga); carga = 0;
  const temBola = bola.dono === p, perto = !bola.dono && Math.hypot(bola.x - p.x, bola.y - p.y) < 26;
  if (!temBola && !perto) return;
  let ang = p.ang;
  if (!forte) { let melhor = null, md = .35; for (const q of jog) if (q.t === 0 && q !== p) { const d = Math.abs(difAng(p.ang, angPara(p, q))); if (d < md) { md = d; melhor = q; } }
    if (melhor) ang = angPara(p, melhor); chute(p, 230 + 400*c, ang); }
  else { chute(p, 470 + 560*c, ang + (Math.random() - .5)*.06); return; }
  if (autoTroca) { const rec = recebedor(p); if (rec) { sel = rec.n; bip(900, .03, 'sine', .03); } }
}
function recebedor(passador){ // companheiro mais perto do caminho da bola
  const v = Math.hypot(bola.vx, bola.vy) || 1, alcance = v/0.97;
  let melhor = null, md = 1e9;
  for (const q of jog) { if (q.t !== 0 || q === passador || q.gk) continue;
    const s = Math.max(0, Math.min(alcance, (q.x - bola.x)*bola.vx/v + (q.y - bola.y)*bola.vy/v));
    const d = Math.hypot(bola.x + bola.vx/v*s - q.x, bola.y + bola.vy/v*s - q.y) + s*.15; if (d < md) { md = d; melhor = q; } }
  return melhor; }
const MAPA_F = {ArrowLeft: 'esq', KeyA: 'esq', ArrowRight: 'dir', KeyD: 'dir', Space: 'acao', ArrowUp: 'passe', KeyW: 'passe', ArrowDown: 'chute', KeyS: 'chute', KeyE: 'esquema'};
addEventListener('keydown', e => {
  if (/^(Digit|Numpad)[1-6]$/.test(e.code)) { sel = +e.code.slice(-1); bip(900, .03, 'sine', .03); return; }
  if (e.code === 'KeyT') { autoTroca = !autoTroca; aviso('Troca automática ' + (autoTroca ? 'LIGADA' : 'DESLIGADA')); return; }
  if (e.code === 'KeyP' && (estado === 'jogando' || estado === 'pausa')) { estado = estado === 'pausa' ? 'jogando' : 'pausa'; tela(estado === 'pausa' ? '<h1>⏸️ Pausa</h1><p>Aperte P para continuar</p>' : null); return; }
  const k = MAPA_F[e.code]; if (!k) { if (e.code === 'Enter' && estado !== 'jogando') { const b = $('bj'); if (b) b.click(); } return; }
  e.preventDefault(); if (e.repeat) return;
  if (k === 'acao' && estado !== 'jogando' && estado !== 'gol') { const b = $('bj'); if (b) { b.click(); return; } }
  teclas[k] = true; if (k === 'passe' || k === 'chute') carga = 0; });
addEventListener('keyup', e => { const k = MAPA_F[e.code]; if (!k) return; e.preventDefault();
  if (teclas[k] && (k === 'passe' || k === 'chute')) soltarPasse(k === 'chute'); teclas[k] = false; });
document.querySelectorAll('[data-k]').forEach(b => { const k = b.dataset.k;
  b.addEventListener('pointerdown', e => { e.preventDefault(); b.setPointerCapture(e.pointerId); teclas[k] = true; if (k === 'passe' || k === 'chute') carga = 0; audio(); });
  const solta = () => { if (teclas[k] && (k === 'passe' || k === 'chute')) soltarPasse(k === 'chute'); teclas[k] = false; };
  ['pointerup', 'pointercancel'].forEach(t => b.addEventListener(t, solta)); });
cv.addEventListener('pointerdown', e => { cv.focus(); const r = cv.getBoundingClientRect(), x = (e.clientX - r.left)/r.width*W, y = (e.clientY - r.top)/r.height*H;
  const [p, d] = maisPerto(jog.filter(q => q.t === 0), x, y); if (p && d < 34) { sel = p.n; bip(900, .03, 'sine', .03); } });
// ---------- inteligência
function noMeuLado(t, x, y){ return t === 0 ? [(x - CX)/CW, (y - CY)/CH] : [1 - (x - CX)/CW, 1 - (y - CY)/CH]; }
function atualizarFases(dt){ for (let t = 0; t < 2; t++) { let alvo;
    if (bola.dono) alvo = bola.dono.t === t ? 1 : 0; else alvo = bola.ultimo && bola.ultimo.t === t ? .6 : .35;
    faseT[t] += (alvo - faseT[t])*Math.min(1, dt*(alvo > faseT[t] ? 1.3 : 2.2)); } }
function posTatica(p){
  const [bx, yd, ya, folga] = PAPEIS[p.n], f = faseT[p.t], [bfx, bfy] = noMeuLado(p.t, bola.x, bola.y), ala = p.n === 3 || p.n === 4;
  let fy = yd + (ya - yd)*f + (bfy - .5)*.13;
  let fx = bx + (bfx - .5)*(ala ? .06 : .2); fx = Math.max(bx - folga, Math.min(bx + folga, fx));
  if (ala && f > .6) fx = bx + (bx < .5 ? -.05 : .05);            // alas abrem o campo no ataque
  if (p.n === 2) fy = Math.max(fy, .52);                          // o fixo nunca passa muito do meio
  if (p.n === 6 && f < .4) fy = Math.min(fy, .6);                 // o pivô fica adiantado, pronto para o contra-ataque
  p.jt -= 1/60; if (p.jt <= 0) { p.jt = 1.2 + Math.random()*2; p.jx = (Math.random() - .5)*.05; p.jy = (Math.random() - .5)*.04; }
  fx += p.jx; fy += p.jy; fx = Math.max(.06, Math.min(.94, fx)); fy = Math.max(.07, Math.min(.93, fy));
  let [x, y] = posForm(fx, fy, p.t);
  if (f < .4) { // sem a bola: marca o adversário que entrar na sua zona
    const adv = jog.filter(o => o.t !== p.t && !o.gk && o !== bola.dono), [o, d] = maisPerto(adv, x, y);
    if (o && d < 115) { const gy = p.t === 0 ? BASE : TOPO; const mx = o.x + (MEIO - o.x)*.15, my = o.y + (gy - o.y)*.18; x = x*.4 + mx*.6; y = y*.4 + my*.6; } }
  p.tx = x; p.ty = y; return [x, y]; }
function funcaoDefesa(p){ // quem pressiona e quem faz a cobertura
  const t = p.t, [, bfy] = noMeuLado(t, bola.x, bola.y), excl = t === 0 ? sel : -1;
  const cand = jog.filter(q => q.t === t && !q.gk && q.n !== excl);
  const [pressao] = maisPerto(cand, bola.x, bola.y);
  if (p === pressao) return 'pressiona';
  return null; }
function goleiro(p, dt){ const linha = p.t === 0 ? BASE - 20 : TOPO + 20, f = p.t === 1 ? F().f : 1;
  let alvoX = MEIO + (bola.x - MEIO)*.45;
  const vemPraCa = p.t === 0 ? bola.vy > 60 : bola.vy < -60;
  if (!bola.dono && vemPraCa) { const tt = (linha - bola.y)/bola.vy; if (tt > 0 && tt < 1.5) alvoX = bola.x + bola.vx*tt; }
  alvoX = Math.max(MEIO - GOL/2 + 6, Math.min(MEIO + GOL/2 - 6, alvoX));
  const sai = !bola.dono && Math.hypot(bola.x - p.x, bola.y - p.y) < 70 && Math.abs(bola.y - linha) < 90 && Math.hypot(bola.vx, bola.vy) < 160;
  if (sai) mover(p, bola.x, bola.y, 150*f, dt); else mover(p, alvoX, linha, 150*f, dt);
  if (bola.dono === p) { p.segura += dt; p.vx = p.vy = 0; p.ang = p.t === 0 ? -Math.PI/2 : Math.PI/2;
    if (p.segura > .9) { const adv = jog.filter(q => q.t !== p.t);
      const ops = jog.filter(q => q.t === p.t && !q.gk).map(q => ({q, livre: maisPerto(adv, q.x, q.y)[1], d: Math.hypot(q.x - p.x, q.y - p.y),
          bloq: adv.some(h => { const dd = Math.hypot(q.x - p.x, q.y - p.y), t = ((h.x - p.x)*(q.x - p.x) + (h.y - p.y)*(q.y - p.y))/(dd*dd);
            return t > .1 && t < .95 && Math.hypot(p.x + (q.x - p.x)*t - h.x, p.y + (q.y - p.y)*t - h.y) < 26; })}))
        .sort((a, b) => (b.livre - (b.bloq ? 80 : 0)) - (a.livre - (a.bloq ? 80 : 0)));
      if ((ops.length && !ops[0].bloq && ops[0].livre > 90) || p.segura > 2) { const alvo = ops[0].q;
        const d = Math.hypot(alvo.x - p.x, alvo.y - p.y); p.ang = angPara(p, alvo); p.segura = 0; chute(p, Math.min(640, d*1.15 + 150), p.ang); } } } else p.segura = 0; }
function ia(p, dt){
  const f = F().f, gy = BASE + 4;
  if (p.gk) return goleiro(p, dt);
  if (bola.dono === p) {
    p.pensa -= dt; const hum = jog.filter(q => q.t === 0); const [q, dq] = maisPerto(hum, p.x, p.y), dGol = Math.hypot(MEIO - p.x, gy - p.y);
    if (p.pensa <= 0) { p.pensa = .35;
      if (dGol < 270 && Math.random() < .8) { const gkH = jog.find(o => o.t === 0 && o.gk);
        const cantoX = fase >= 2 ? (gkH.x > MEIO ? MEIO - GOL/2 + 14 : MEIO + GOL/2 - 14) : MEIO + (Math.random() - .5)*GOL*.8;   // nas fases finais mira no canto
        const alvo = Math.atan2(gy - p.y, cantoX - p.x) + (Math.random() - .5)*2*F().erro; p.ang = alvo; chute(p, 620 + fase*70 + Math.random()*200, alvo); return; }
      const op = jog.filter(o => o.t === 1 && o !== p && !o.gk).map(o => {
          const d = Math.hypot(o.x - p.x, o.y - p.y), livre = maisPerto(hum, o.x, o.y)[1];
          // linha de passe livre? nenhum adversário perto do caminho da bola
          const bloqueado = hum.some(h => { const t = ((h.x - p.x)*(o.x - p.x) + (h.y - p.y)*(o.y - p.y))/(d*d); if (t < .1 || t > .95) return false;
            return Math.hypot(p.x + (o.x - p.x)*t - h.x, p.y + (o.y - p.y)*t - h.y) < 22; });
          return {o, d, livre, bloqueado, avanco: o.y - p.y, nota: Math.min(livre, 120)*.35 + (o.y - p.y)*1.0 - Math.abs(d - 170)*.15 + (o.n === 6 ? 35 : 0)}; })
        .filter(x => !x.bloqueado && x.livre > 35 && x.d > 60 && (x.avanco > -50 || dq < 55)).sort((a, b) => b.nota - a.nota);
      if (op.length) { const o = op[0].o, a = angPara(p, o) + (Math.random() - .5)*F().erro*.5; p.ang = a; chute(p, Math.min(600, op[0].d*1.2 + 130), a); return; } }
    let alvo = Math.atan2(gy - p.y, MEIO - p.x);   // sem passe livre: conduz devagar e protege a bola
    if (q && dq < 60) alvo += difAng(angPara(p, q), alvo) > 0 ? .6 : -.6;
    girarPara(p, alvo, 3.5*f, dt); const v = ANDA*.8*f; p.vx = Math.cos(p.ang)*v; p.vy = Math.sin(p.ang)*v; return; }
  if (!(bola.dono && bola.dono.t === 1)) { const papel = funcaoDefesa(p);
    if (papel === 'pressiona') { mover(p, bola.x + bola.vx*.25, bola.y + bola.vy*.25, (bola.dono ? ANDA*1.15 : CORRE)*f, dt); return; } }
  if (p.fica > 0) { p.vx *= .85; p.vy *= .85; return; }
  const [x, y] = posTatica(p); mover(p, x, y, (Math.hypot(x - p.x, y - p.y) > 120 ? ANDA*1.2 : ANDA*.75)*f, dt); }
function companheiro(p, dt){
  if (p.gk) return goleiro(p, dt);
  if (bola.dono === p) { p.vx *= .8; p.vy *= .8; girarPara(p, -Math.PI/2, 3, dt); return; }
  if (!bola.dono && bola.ultimo && bola.ultimo.t === 0 && Math.hypot(bola.vx, bola.vy) > 40) {  // vai dominar o passe
    const para = [bola.x + bola.vx*.95, bola.y + bola.vy*.95], cands = jog.filter(q => q.t === 0 && !q.gk && q !== bola.ultimo && q.n !== sel);
    const [rec] = maisPerto(cands, para[0], para[1]);
    if (rec === p) { const [ix, iy] = maisPertoDaLinha(p); mover(p, ix, iy, ANDA*1.3, dt); return; } }
  if (!(bola.dono && bola.dono.t === 0)) { const papel = funcaoDefesa(p), perto = Math.hypot(bola.x - p.x, bola.y - p.y) < 150;
    if (papel === 'pressiona' && (perto || bola.y > CENTRO)) { mover(p, bola.x + bola.vx*.25, bola.y + bola.vy*.25, bola.dono ? ANDA*1.1 : CORRE, dt); return; } }
  if (p.fica > 0) { p.vx *= .85; p.vy *= .85; return; }
  const [x, y] = posTatica(p); mover(p, x, y, Math.hypot(x - p.x, y - p.y) > 120 ? ANDA*1.2 : ANDA*.75, dt); }
function maisPertoDaLinha(p){ const v = Math.hypot(bola.vx, bola.vy) || 1, ux = bola.vx/v, uy = bola.vy/v;
  const s = Math.max(0, (p.x - bola.x)*ux + (p.y - bola.y)*uy); return [bola.x + ux*s, bola.y + uy*s]; }
// ---------- física
function atualizar(dt){
  msgT -= dt; for (const q of part) { q.x += q.vx*dt; q.y += q.vy*dt; q.vy += 300*dt; q.t -= dt; } part = part.filter(q => q.t > 0); tremor = Math.max(0, tremor - dt);
  if (estado === 'gol') { timer -= dt; if (timer <= 0) { if (ouro) return fimPartida(); estado = 'jogando'; saida(saidaTime); } return; }
  if (estado !== 'jogando') return;
  if (!ouro) { relogio -= dt; if (relogio <= 0) { relogio = 0; if (placar[0] === placar[1]) { ouro = true; aviso('⚡ EMPATE! GOL DE OURO: quem marcar vence!', 3); apito(); } else return fimPartida(); } }
  const p = meu(sel);
  if (p) { if (teclas.esq) p.ang -= 3.6*dt; if (teclas.dir) p.ang += 3.6*dt;
    const passeVindo = !bola.dono && bola.ultimo && bola.ultimo.t === 0 && bola.ultimo !== p && Math.hypot(bola.vx, bola.vy) > 40;
    if (passeVindo && !teclas.acao && !teclas.esq && !teclas.dir) { const [ix, iy] = maisPertoDaLinha(p); mover(p, ix, iy, ANDA*1.3, dt); }
    else if (teclas.acao && !saidaPendente) { tEspaco += dt; const v = (tEspaco > .35 ? CORRE : ANDA)*(bola.dono === p && tEspaco > .35 ? .82 : 1); p.vx = Math.cos(p.ang)*v; p.vy = Math.sin(p.ang)*v; } else { tEspaco = 0; p.vx *= .75; p.vy *= .75; }
    if (teclas.passe || teclas.chute) carga = Math.min(1, carga + dt*1.1); }
  if (saidaPendente) {
    const k = bola.dono;
    if (!k || k !== bola.ultimo) saidaPendente = false;
    else { for (const q of jog) if (q !== k) { q.vx = q.vy = 0; }
      if (k.t === 0) { k.vx = k.vy = 0; if (k !== p) { girarPara(k, -Math.PI/2, 3, dt); } }
      else { saidaT -= dt; k.vx = k.vy = 0; if (saidaT <= 0) { const alvo = jog.filter(o => o.t === 1 && [5, 3, 4].includes(o.n))[Math.floor(Math.random()*3)];
          const a = angPara(k, alvo); k.ang = a; chute(k, Math.min(560, Math.hypot(alvo.x - k.x, alvo.y - k.y)*1.2 + 130), a); } } }
  }
  if (saidaPendente) { for (const q of jog) { q.x += q.vx*dt; q.y += q.vy*dt; } if (bola.dono) { const d = bola.dono; bola.x = d.x + Math.cos(d.ang)*14; bola.y = d.y + Math.sin(d.ang)*14; } return; }
  atualizarFases(dt);
  for (const q of jog) { q.cd = Math.max(0, q.cd - dt); q.fica = Math.max(0, (q.fica || 0) - dt); if (q === p) continue; if (q.t === 1) ia(q, dt); else companheiro(q, dt); }
  for (const q of jog) { q.x += q.vx*dt; q.y += q.vy*dt;
    const minY = q.gk ? (q.t === 0 ? BASE - 120 : TOPO + 10) : TOPO + 12, maxY = q.gk ? (q.t === 0 ? BASE - 10 : TOPO + 120) : BASE - 12;
    q.x = Math.max(CX + 12, Math.min(CX + CW - 12, q.x)); q.y = Math.max(minY, Math.min(maxY, q.y)); }
  for (let i = 0; i < jog.length; i++) for (let j = i + 1; j < jog.length; j++) { const a = jog[i], b = jog[j], dx = b.x - a.x, dy = b.y - a.y, d = Math.hypot(dx, dy);
    if (d < 22 && d > .01) { const e = (22 - d)/2, nx = dx/d, ny = dy/d; a.x -= nx*e; a.y -= ny*e; b.x += nx*e; b.y += ny*e; } }
  // bola
  if (bola.dono) { const d = bola.dono, adiante = 14 + Math.min(10, Math.hypot(d.vx, d.vy)/18);
    bola.x = d.x + Math.cos(d.ang)*adiante; bola.y = d.y + Math.sin(d.ang)*adiante; bola.vx = d.vx; bola.vy = d.vy; bola.giro += Math.hypot(d.vx, d.vy)*dt*.1;
    if (!d.gk) for (const q of jog) if (q.t !== d.t && !q.gk && Math.hypot(q.x - bola.x, q.y - bola.y) < 20) {
      const chance = q.t === 0 ? (q.n === sel ? 2.4 : .8) : F().roubo*1.6;
      if (Math.random() < chance*dt) { d.cd = .5; bola.dono = null; bola.vx = Math.cos(q.ang)*120; bola.vy = Math.sin(q.ang)*120; bip(300, .05, 'square', .04); if (q.t === 0 && autoTroca) sel = q.n; break; } } }
  else { const bx0 = bola.x, by0 = bola.y; bola.x += bola.vx*dt; bola.y += bola.vy*dt;
    if (goleiroPega(bx0, by0)) return;
    const at = Math.pow(.38, dt); bola.vx *= at; bola.vy *= at; bola.giro += Math.hypot(bola.vx, bola.vy)*dt*.1;
    if (bola.x < CX + 6) { bola.x = CX + 6; bola.vx = Math.abs(bola.vx)*.6; } if (bola.x > CX + CW - 6) { bola.x = CX + CW - 6; bola.vx = -Math.abs(bola.vx)*.6; }
    const naBoca = Math.abs(bola.x - MEIO) < GOL/2 - 5;
    if (bola.y < TOPO + 6) { if (naBoca && bola.y < TOPO - 4) return gol(0); if (!naBoca) { bola.y = TOPO + 6; bola.vy = Math.abs(bola.vy)*.6; } }
    if (bola.y > BASE - 6) { if (naBoca && bola.y > BASE + 4) return gol(1); if (!naBoca) { bola.y = BASE - 6; bola.vy = -Math.abs(bola.vy)*.6; } }
    if (Math.abs(bola.x - MEIO) >= GOL/2 - 5 && (bola.y < TOPO || bola.y > BASE)) { bola.vx = -bola.vx*.5; bola.x = MEIO + Math.sign(bola.x - MEIO)*(GOL/2 - 7); }
    const vel = Math.hypot(bola.vx, bola.vy);
    for (const q of jog) { if (q.cd > 0) continue; const d = Math.hypot(q.x - bola.x, q.y - bola.y); if (d > (q.gk ? 24 : 18)) continue;
      const limite = q.gk ? (q.t === 0 ? 680 : F().gk) : 470;
      if (vel < limite) { const deTime = bola.ultimo && bola.ultimo.t === q.t && bola.ultimo !== q; bola.dono = q; q.cd = 0; bola.ultimo = q; if (q.t === 1) q.pensa = F().pensa + .25;
        if (q.t === 0 && autoTroca && (deTime || q.n !== sel) && !q.gk) sel = q.n;
        if (q.gk && vel > 200) { bip(500, .08, 'triangle', .05); aviso(q.t === 0 ? '🧤 Defesa do seu goleiro!' : '🧤 Que defesa do goleiro!', 1); } break; }
      else { const nx = (bola.x - q.x)/(d || 1), ny = (bola.y - q.y)/(d || 1), vn = bola.vx*nx + bola.vy*ny; if (vn < 0) { bola.vx = (bola.vx - 2*vn*nx)*.45; bola.vy = (bola.vy - 2*vn*ny)*.45; }
        q.cd = .2; bip(200, .05, 'triangle', .05); if (q.gk) aviso('🧤 Espalmou!', 1); break; } } }
}
function distSeg(px, py, ax, ay, bx, by){ const dx = bx - ax, dy = by - ay, L = dx*dx + dy*dy || 1, t = Math.max(0, Math.min(1, ((px - ax)*dx + (py - ay)*dy)/L));
  return Math.hypot(ax + dx*t - px, ay + dy*t - py); }
function goleiroPega(bx0, by0){ // colisão contínua: a bola não "atravessa" o goleiro entre dois quadros
  const vel = Math.hypot(bola.vx, bola.vy);
  for (const g of jog) { if (!g.gk || (bola.ultimo && bola.ultimo === g)) continue;
    if (distSeg(g.x, g.y, bx0, by0, bola.x, bola.y) > 21) continue;
    const limite = g.t === 0 ? 680 : F().gk;
    if (vel < limite) { bola.dono = g; bola.ultimo = g; g.cd = 0; if (vel > 200) { bip(500, .08, 'triangle', .05); aviso(g.t === 0 ? '🧤 Defesa do seu goleiro!' : '🧤 Que defesa do goleiro!', 1); } }
    else { const sinal = g.t === 0 ? -1 : 1, lado = bola.x < MEIO ? -1 : 1;   // espalma para a lateral, longe da área
      bola.x = g.x + lado*14; bola.y = g.y + sinal*10; bola.vx = lado*(320 + Math.random()*160); bola.vy = sinal*(120 + Math.random()*120); g.cd = .15;
      bip(200, .05, 'triangle', .05); aviso('🧤 Espalmou!', 1); }
    return true; }
  return false; }
function gol(time){ placar[time]++; estado = 'gol'; timer = 2.4; saidaTime = 1 - time; tremor = .5;
  aviso(time === 0 ? '⚽ GOOOOL! Seu time marcou!' : '😱 Gol de ' + F().adv, 2.4); vibrar(time === 0 ? [80, 60, 80] : 200);
  if (time === 0) { acorde([523, 659, 784, 1046, 1318], .18); ruido(1.6, .1); for (let i = 0; i < 120; i++) part.push({x: MEIO + (Math.random() - .5)*GOL, y: TOPO, vx: (Math.random() - .5)*400, vy: Math.random()*-300 + 60, t: 1.5 + Math.random(), cor: ['#ffd34d', '#4fc3ff', '#fff', '#5be08a'][i % 4]}); }
  else bip(160, .5, 'sawtooth', .05); }
function fimPartida(){ estado = 'entre'; const venceu = placar[0] > placar[1]; campanha[fase] = placar.slice(); apito(); setTimeout(apito, 400);
  if (venceu && fase === 3) { estado = 'campeao'; salvarRecorde('rec_futsal_titulos', lerRecorde('rec_futsal_titulos') + 1); acorde([523, 659, 784, 1046, 1318, 1568], .2);
    for (let i = 0; i < 200; i++) part.push({x: Math.random()*W, y: -10, vx: (Math.random() - .5)*80, vy: Math.random()*200, t: 3 + Math.random()*2, cor: ['#ffd34d', '#4fc3ff', '#fff', '#ff5ea8'][i % 4]});
    tela('<h1>🏆 CAMPEÃO!</h1><p class="grande">Final: ' + placar[0] + ' x ' + placar[1] + ' contra os ' + F().adv + '</p>' + chave() + '<p>Títulos conquistados: ' + lerRecorde('rec_futsal_titulos') + ' 🏆</p><button id="bj">🔁 Jogar a Copa de novo</button>');
    $('bj').onclick = () => { fase = 0; campanha = []; novaPartida(); }; return; }
  if (venceu) { tela('<h1>✅ Classificado!</h1><p class="grande">' + placar[0] + ' x ' + placar[1] + '</p><p>Você eliminou os ' + F().adv + '.</p>' + chave(fase + 1) + '<button id="bj">▶️ Jogar ' + FASES[fase + 1].nome + '</button>');
    $('bj').onclick = () => { fase++; novaPartida(); }; }
  else { tela('<h1>❌ Eliminado</h1><p class="grande">' + placar[0] + ' x ' + placar[1] + '</p><p>Fim da linha nas ' + F().nome.toLowerCase() + '. Os ' + F().adv + ' venceram.</p>' + chave() + '<button id="bj">🔁 Recomeçar a Copa</button>');
    $('bj').onclick = () => { fase = 0; campanha = []; novaPartida(); }; } }
function chave(prox){ return '<div style="text-align:left;margin:8px auto;max-width:300px;line-height:1.7">' + FASES.map((x, i) => {
  const r = campanha[i]; const ic = r ? (r[0] > r[1] ? '✅' : '❌') : i === prox || (prox === undefined && i === fase && !r) ? '▶️' : '🔒';
  return ic + ' <b>' + x.nome + '</b>: ' + x.adv + (r ? ' (' + r[0] + 'x' + r[1] + ')' : ''); }).join('<br>') + '</div>'; }
// ---------- desenho
function quadra(){
  ctx.fillStyle = '#1b2a1f'; ctx.fillRect(0, 0, W, H);
  for (let i = 0; i < 12; i++) { ctx.fillStyle = i % 2 ? '#c98b4f' : '#c4844a'; ctx.fillRect(CX, CY + i*CH/12, CW, CH/12 + 1); }
  ctx.fillStyle = 'rgba(30,90,170,.25)'; area(false, true); area(true, true);
  ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.strokeRect(CX, CY, CW, CH);
  ctx.beginPath(); ctx.moveTo(CX, CENTRO); ctx.lineTo(CX + CW, CENTRO); ctx.stroke();
  ctx.beginPath(); ctx.arc(MEIO, CENTRO, 60, 0, 7); ctx.stroke(); ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(MEIO, CENTRO, 4, 0, 7); ctx.fill();
  area(false); area(true);
  [[TOPO + 100], [TOPO + 165], [BASE - 100], [BASE - 165]].forEach(([y]) => { ctx.beginPath(); ctx.arc(MEIO, y, 3, 0, 7); ctx.fill(); });
  for (const [y, s] of [[TOPO, -1], [BASE, 1]]) { ctx.fillStyle = 'rgba(255,255,255,.18)'; ctx.fillRect(MEIO - GOL/2, s < 0 ? y - 24 : y, GOL, 24);
    ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 1; for (let x = MEIO - GOL/2; x <= MEIO + GOL/2; x += 8) { ctx.beginPath(); ctx.moveTo(x, y); ctx.lineTo(x, y + s*24); ctx.stroke(); }
    for (let k = 0; k <= 24; k += 8) { ctx.beginPath(); ctx.moveTo(MEIO - GOL/2, y + s*k); ctx.lineTo(MEIO + GOL/2, y + s*k); ctx.stroke(); }
    ctx.strokeStyle = '#eee'; ctx.lineWidth = 5; ctx.beginPath(); ctx.moveTo(MEIO - GOL/2, y); ctx.lineTo(MEIO - GOL/2, y + s*24); ctx.lineTo(MEIO + GOL/2, y + s*24); ctx.lineTo(MEIO + GOL/2, y); ctx.stroke(); }
  ctx.lineWidth = 1; }
function area(baixo, preencher){ ctx.save(); if (baixo) { ctx.translate(0, CY*2 + CH); ctx.scale(1, -1); }
  ctx.beginPath(); ctx.moveTo(MEIO - GOL/2 + 10 - 90, TOPO); ctx.arc(MEIO - GOL/2 + 10, TOPO, 90, Math.PI, Math.PI/2, true);
  ctx.lineTo(MEIO + GOL/2 - 10, TOPO + 90); ctx.arc(MEIO + GOL/2 - 10, TOPO, 90, Math.PI/2, 0, true);
  if (preencher) { ctx.closePath(); ctx.fill(); } else { ctx.strokeStyle = '#fff'; ctx.lineWidth = 3; ctx.stroke(); } ctx.restore(); }
function jogador(p, rel){
  const cor = p.t === 0 ? (p.gk ? '#2e7d32' : '#1e63d6') : (p.gk ? '#ef6c00' : F().cor), selec = p.t === 0 && p.n === sel;
  ctx.fillStyle = 'rgba(0,0,0,.25)'; ctx.beginPath(); ctx.ellipse(p.x + 3, p.y + 4, 14, 11, 0, 0, 7); ctx.fill();
  if (selec) { ctx.strokeStyle = `rgba(255,214,10,${.6 + Math.sin(rel*8)*.4})`; ctx.lineWidth = 3; ctx.beginPath(); ctx.arc(p.x, p.y, 20, 0, 7); ctx.stroke();
    const forca = (teclas.passe || teclas.chute) ? carga : 0, comp = 34 + forca*40;
    ctx.strokeStyle = teclas.chute ? '#ff5252' : '#ffd60a'; ctx.lineWidth = 3; ctx.setLineDash([6, 5]); ctx.beginPath(); ctx.moveTo(p.x, p.y);
    ctx.lineTo(p.x + Math.cos(p.ang)*comp, p.y + Math.sin(p.ang)*comp); ctx.stroke(); ctx.setLineDash([]);
    const ax = p.x + Math.cos(p.ang)*comp, ay = p.y + Math.sin(p.ang)*comp; ctx.fillStyle = ctx.strokeStyle; ctx.beginPath();
    ctx.moveTo(ax + Math.cos(p.ang)*8, ay + Math.sin(p.ang)*8); ctx.lineTo(ax + Math.cos(p.ang + 2.4)*8, ay + Math.sin(p.ang + 2.4)*8); ctx.lineTo(ax + Math.cos(p.ang - 2.4)*8, ay + Math.sin(p.ang - 2.4)*8); ctx.fill();
    if (forca > 0) { ctx.strokeStyle = forca > .8 ? '#ff5252' : '#5be08a'; ctx.lineWidth = 4; ctx.beginPath(); ctx.arc(p.x, p.y, 25, -Math.PI/2, -Math.PI/2 + forca*2*Math.PI); ctx.stroke(); } }
  const passo = Math.sin(rel*14 + p.n)*Math.min(1, Math.hypot(p.vx, p.vy)/60)*5;
  ctx.save(); ctx.translate(p.x, p.y); ctx.rotate(p.ang);
  ctx.fillStyle = '#222'; ctx.beginPath(); ctx.ellipse(4 + passo, -6, 5, 3.5, 0, 0, 7); ctx.ellipse(4 - passo, 6, 5, 3.5, 0, 0, 7); ctx.fill();
  ctx.fillStyle = cor; ctx.beginPath(); ctx.ellipse(0, 0, 9, 13, 0, 0, 7); ctx.fill(); ctx.strokeStyle = 'rgba(0,0,0,.35)'; ctx.lineWidth = 2; ctx.stroke();
  ctx.restore();
  ctx.fillStyle = p.t === 0 ? '#fff' : '#ffe0c2'; ctx.beginPath(); ctx.arc(p.x, p.y, 9, 0, 7); ctx.fill(); ctx.strokeStyle = cor; ctx.lineWidth = 2; ctx.stroke();
  ctx.fillStyle = p.t === 0 ? '#0d47a1' : '#111'; ctx.font = 'bold 13px system-ui'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(p.n, p.x, p.y + 1); ctx.textBaseline = 'alphabetic';
  if (p.t === 0) { ctx.font = 'bold 9px system-ui'; ctx.fillStyle = selec ? '#ffd60a' : 'rgba(255,255,255,.85)'; ctx.fillText(PAPEIS[p.n][4], p.x, p.y + 25); } }
function desenhar(rel){
  ctx.save(); if (tremor) ctx.translate((Math.random() - .5)*tremor*14, (Math.random() - .5)*tremor*14);
  quadra(); if (!bola) { ctx.restore(); return; }
  const vb = Math.hypot(bola.vx, bola.vy);
  if (!bola.dono && vb > 250) { ctx.strokeStyle = 'rgba(255,255,255,.35)'; ctx.lineWidth = 6; ctx.beginPath(); ctx.moveTo(bola.x, bola.y); ctx.lineTo(bola.x - bola.vx*.05, bola.y - bola.vy*.05); ctx.stroke(); }
  if (teclas.esquema) { ctx.setLineDash([4, 4]); for (const p of jog.filter(q => q.t === 0 && !q.gk)) { const [x, y] = posTatica(p);
      ctx.strokeStyle = 'rgba(255,255,255,.7)'; ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(x, y); ctx.stroke(); ctx.fillStyle = 'rgba(79,195,255,.6)';
      ctx.beginPath(); ctx.arc(x, y, 8, 0, 7); ctx.fill(); ctx.fillStyle = '#fff'; ctx.font = 'bold 10px system-ui'; ctx.textAlign = 'center'; ctx.fillText(PAPEIS[p.n][5], x, y - 12); }
    ctx.setLineDash([]); }
  [...jog].sort((a, b) => a.y - b.y).forEach(p => jogador(p, rel));
  ctx.fillStyle = 'rgba(0,0,0,.3)'; ctx.beginPath(); ctx.ellipse(bola.x + 2, bola.y + 3, 7, 5, 0, 0, 7); ctx.fill();
  ctx.fillStyle = '#fff'; ctx.beginPath(); ctx.arc(bola.x, bola.y, 7, 0, 7); ctx.fill(); ctx.strokeStyle = '#333'; ctx.lineWidth = 1; ctx.stroke();
  ctx.fillStyle = '#222'; for (let k = 0; k < 3; k++) { const a = bola.giro + k*2.1; ctx.beginPath(); ctx.arc(bola.x + Math.cos(a)*3.5, bola.y + Math.sin(a)*3.5, 1.8, 0, 7); ctx.fill(); }
  for (const q of part) { ctx.globalAlpha = Math.min(1, q.t); ctx.fillStyle = q.cor; ctx.fillRect(q.x - 3, q.y - 2, 6, 4); } ctx.globalAlpha = 1;
  ctx.restore();
  // placar
  const g = ctx.createLinearGradient(0, 0, W, 0); g.addColorStop(0, '#0d2b6b'); g.addColorStop(.5, '#111827'); g.addColorStop(1, F().cor);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, 52);
  ctx.textAlign = 'left'; ctx.fillStyle = '#fff'; ctx.font = 'bold 15px system-ui'; ctx.fillText('🔵 VOCÊ', 12, 22); ctx.textAlign = 'right'; ctx.fillText(F().adv.toUpperCase().slice(0, 19), W - 50, 22);
  ctx.textAlign = 'center'; ctx.font = 'bold 28px system-ui'; ctx.fillText(placar[0] + ' x ' + placar[1], W/2, 32);
  ctx.font = 'bold 12px system-ui'; ctx.fillStyle = ouro ? '#ffd34d' : '#cfd6ff';
  const mm = Math.floor(relogio/60), ss = String(Math.floor(relogio % 60)).padStart(2, '0');
  ctx.fillText(ouro ? '⚡ GOL DE OURO' : '⏱ ' + mm + ':' + ss, W/2, 47); ctx.textAlign = 'left'; ctx.fillStyle = '#9fb3ff'; ctx.fillText(F().nome, 12, 43);
  ctx.textAlign = 'right'; ctx.fillText('troca auto ' + (autoTroca ? 'ON' : 'OFF') + ' (T)', W - 50, 43);
  if (msgT > 0) { ctx.globalAlpha = Math.min(1, msgT*2); ctx.fillStyle = 'rgba(0,0,0,.55)'; ctx.fillRect(0, CENTRO - 26, W, 44); ctx.textAlign = 'center'; ctx.fillStyle = '#ffd34d';
    ctx.font = 'bold 20px system-ui'; ctx.fillText(msg, W/2, CENTRO + 3); ctx.globalAlpha = 1; }
  ctx.textAlign = 'center'; ctx.font = '600 12px system-ui'; ctx.fillStyle = 'rgba(255,255,255,.6)';
  ctx.fillText('1–6 seleciona · ← → gira · ESPAÇO anda/corre · ↑ passe · ↓ chute · E esquema', W/2, H - 8); }
let ult = performance.now(), rel = 0;
function loop(t){ const dt = Math.min(.033, (t - ult)/1000); ult = t; rel += dt; atualizar(dt); desenhar(rel); requestAnimationFrame(loop); }
criarTimes(); saida(0); estado = 'inicio';
tela('<h1>⚽ Copa de Futsal</h1><p>Você é o time <b style="color:#4fc3ff">azul</b> e ataca para <b>cima</b>. São 4 jogos, das <b>oitavas à final</b>, cada um mais difícil que o anterior!</p>' +
  '<p><b>1 a 6</b> ou clique no número = escolher jogador<br><b>← →</b> girar · <b>ESPAÇO</b> andar (segure para correr)<br><b>↑</b> passe · <b>↓</b> chute (segure para mais força)</p>' +
  '<p>Para passar: mire no companheiro e aperte ↑. <b>Quem vai receber a bola ganha vida sozinho</b>, e você também pode trocar pelos números. (Tecla T desliga a troca automática.)</p>' +
  '<p>📋 <b>Esquema 1-3-1:</b> 1 Goleiro · 2 Fixo · 3 e 4 Alas · 5 Meia · 6 Pivô (segure <b>E</b> para ver as posições)</p>' + chave(0) +
  '<p>🏆 Títulos: ' + lerRecorde('rec_futsal_titulos') + '</p><button id="bj">⚽ Entrar em campo</button>');
$('bj').onclick = () => { fase = 0; campanha = []; novaPartida(); }; requestAnimationFrame(loop);
"""
BOTOES_FUTSAL = ('<button data-k="esq">⟲</button><button data-k="dir">⟳</button><button data-k="acao">🏃</button>'
                 '<button data-k="passe">↗️ Passe</button><button data-k="chute">🥅 Chute</button>')


def jogo_futsal():
    jogo_html(pagina_tech(520, TELA_DIV, FUTSAL_JS, BOTOES_FUTSAL, False), 870)
    st.caption("🖱️ No computador, clique no jogo antes de usar o teclado. 📱 No celular, toque no jogador para selecioná-lo e use os botões.")


# =====================================================================
# COMO JOGAR (instruções de cada jogo)
# =====================================================================
COMO_XADREZ = """
**🎯 Objetivo:** dar **xeque-mate** no rei adversário, ou seja, atacar o rei de um jeito que ele não tenha como escapar.

**🖱️ Como mexer aqui:** clique numa peça sua (a casa fica amarela). As **bolinhas** mostram para onde ela pode ir, e os **anéis** mostram peças que ela pode capturar. Depois clique na casa de destino. O computador responde sozinho. As brancas sempre começam.

**♟️ Como cada peça anda:**
- **♟ Peão:** anda **1 casa para frente** (no primeiro movimento pode andar 2). Captura **na diagonal**, 1 casa para frente. Nunca anda para trás.
- **♜ Torre:** quantas casas quiser em **linha reta** (para frente, para trás e para os lados).
- **♝ Bispo:** quantas casas quiser na **diagonal**. Cada bispo fica sempre na mesma cor de casa.
- **♞ Cavalo:** anda em **"L"** (2 casas numa direção e 1 para o lado). É a única peça que **pula** as outras.
- **♛ Dama (rainha):** a peça mais forte. Anda como a torre **e** como o bispo juntos.
- **♚ Rei:** anda **1 casa** em qualquer direção e nunca pode ir para uma casa atacada.

Você **captura** uma peça inimiga parando na casa dela. Não dá para pular em cima das suas próprias peças.

**📏 Regras importantes:**
- **Xeque:** seu rei está sendo atacado (a casa dele fica vermelha). Você é **obrigado** a se livrar do xeque: fugir com o rei, colocar uma peça na frente ou capturar quem está atacando.
- **Xeque-mate:** é um xeque sem saída, e quem levou perde a partida.
- **Afogamento:** quem tem a vez não está em xeque, mas não tem nenhum lance permitido. Isso dá **empate**.
- **Roque:** o rei anda **2 casas** em direção a uma torre, e a torre pula para o outro lado dele. Só vale se o rei e a torre nunca se mexeram, se não houver peças entre eles e se o rei não estiver em xeque nem passar por casa atacada. Aqui, clique no rei e depois na casa 2 para o lado.
- **Promoção:** o peão que chega à última fileira vira outra peça, que você escolhe em *"Promover peão a"* (quase sempre a Dama).
- **En passant:** se um peão inimigo andar 2 casas e parar **ao lado** do seu peão, você pode capturá-lo como se ele tivesse andado só 1. Isso só vale no lance logo em seguida.

**💰 Valor das peças (para pensar nas trocas):** peão = 1 · cavalo = 3 · bispo = 3 · torre = 5 · dama = 9.

**💡 Dicas para começar:**
1. Ocupe o **centro** com peões (casas e4, d4, e5, d5).
2. Tire **cavalos e bispos** de casa logo no começo.
3. Faça o **roque** cedo para proteger o rei.
4. Antes de jogar, pergunte: *"essa peça vai ficar desprotegida?"* e *"o que o adversário está ameaçando?"*
5. Não saia com a dama muito cedo, porque ela vira alvo.
6. Travou num lance? Use o **↩️ Desfazer lance** e tente outro. Comece no nível **Fácil**.
"""

INSTRUCOES = {
    "⚽ Copa de Futsal": """
**🎯 Objetivo:** ser **campeão da Copa**! São 4 jogos eliminatórios contra a IA, cada um mais difícil: **Oitavas → Quartas → Semifinal → Final**. Você é o time **🔵 azul** e ataca **para cima**. Cada partida tem 3 minutos, e em caso de empate vale o **gol de ouro**: quem marcar primeiro vence.

**Controles (teclado):**
- **1 a 6** (ou **clique no número** na cabeça do jogador) escolhe qual jogador você controla. **Só ele se mexe pelo seu comando**, e os outros se movimentam sozinhos, como numa partida de verdade.
- **← →** giram o jogador (a seta amarela mostra para onde ele está mirando).
- **ESPAÇO** segurado faz o jogador **andar**. Continuando a segurar, ele **corre**.
- **↑** é o **passe** e **↓** é o **chute ao gol**. **Segure para dar mais força** (o círculo em volta do jogador enche) e solte para chutar.
- **P** pausa. **E** (segurado) mostra o esquema tático. **T** liga/desliga a troca automática.

**Como tocar a bola, passo a passo:**
1. Gire com ← → até a seta amarela apontar para um companheiro.
2. Aperte **↑** para passar. **Quem vai receber ganha vida na hora** (troca automática) e vai ao encontro da bola sozinho se você não mexer em nada.
3. Agora você já controla quem recebeu: gire, toque de novo ou chute! Os números continuam valendo para trocar quando quiser.

**Ritmo de futsal de verdade:** na **saída de bola** ninguém se mexe até o primeiro passe. Quem toca a bola fica no lugar, só **um** adversário vem marcar e o resto guarda a posição no **esquema 1-3-1** (Goleiro, Fixo, 2 Alas, Meia e Pivô). Jogue no **toque de bola**!

**Dicas de craque:** se a mira estiver **quase** em cima de um companheiro, o passe vai certinho nele. Conduzir a bola correndo é mais lento do que correr sem ela. Para **roubar a bola**, leve o seu jogador selecionado para cima de quem está com ela. O **1** é o goleiro, que defende sozinho, mas você também pode controlá-lo.
""",
    "🌀 Portal Cósmico": """
**🎯 Objetivo:** voar dentro de um **buraco de minhoca** psicodélico, passando **por dentro dos anéis coloridos** e desviando dos **cristais rosa**.

**Controles:** 🖱️ **aponte com o mouse** ou 📱 **com o dedo** (o orbe de luz segue você). No teclado, use as setas.

**Pontos e música:** cada anel atravessado aumenta o **combo**, e cada combo toca uma **nota mais aguda**, formando uma melodia. Errar um anel zera o combo. Com combos altos, a visão **se abre** como em salto para o hiperespaço. Você tem **3 energias 💠**, e cada cristal atingido tira uma.

*Tecnologia: o túnel é desenhado por um **shader GLSL** próprio, um programa que roda na placa de vídeo e calcula as cores de cada pixel em tempo real, com espirais, anéis de luz e cores que mudam a cada nível.*
""",
    "🪐 Estilingue Cósmico": """
**🎯 Objetivo:** lançar o **cometa** ⚪ até o **portal azul** 🌀 usando a **gravidade dos planetas** para fazer curvas, como as sondas espaciais de verdade fazem!

**Como jogar:**
1. **Arraste** para qualquer lado e **puxe para trás**, como um estilingue. A linha rosa mostra a força.
2. A **trilha pontilhada** mostra o **começo** da trajetória. Nos níveis mais altos ela fica mais curta!
3. **Solte** para lançar. Se bater num planeta ou se perder no espaço, tente de novo.
4. Pegue as **✨ poeiras estelares** no caminho.

**Estrelas:** acertar em **1 lançamento** e pegar **todas as poeiras** vale ⭐⭐⭐. Teclas: **R** recomeça o lançamento, e **N** pula o nível depois de 5 tentativas.

*Tecnologia: física gravitacional real (lei de Newton) calculada várias vezes por quadro, com cada planeta puxando o cometa ao mesmo tempo.*
""",
    "🎹 Sinfonia das Estrelas": """
**🎯 Objetivo:** acertar as **notas no tempo certo**. Cada música é **composta pelo computador na hora**, então você nunca vai ouvir a mesma duas vezes!

**Controles:** ⌨️ teclas **D F J K** (uma para cada faixa) ou 📱 **toque nas faixas** e nos botões coloridos. Aperte quando a nota chegar ao **círculo** da faixa dela.

**A mágica:** a bateria, o baixo e os acordes tocam sozinhos, mas **a melodia é você quem toca**. Cada acerto faz soar a nota, e cada nota perdida deixa um buraco na música. 🎶 Cada acerto **perfeito** acende uma **estrela** e desenha uma **constelação** no céu.

**Avaliação:** ✨ Perfeito (300) · 💙 Ótimo (200) · 🙂 Bom (100). A cada 10 acertos seguidos, o multiplicador sobe. No fim você recebe uma nota de **S** a **D**, e com nota de C para cima a próxima música é **mais rápida** e mais difícil.

🔊 **Ligue o som!** Este jogo é feito de música.
""",
    "💎 Joias Encantadas": """
**🎯 Objetivo:** trocar **joias vizinhas** para formar linhas de **3 ou mais iguais** e alcançar a **meta de pontos** (barra no topo) antes de acabarem as jogadas.

**Como jogar:** **arraste** uma joia na direção da vizinha, ou **toque em duas** joias vizinhas. Se a troca não formar uma linha, as joias voltam ao lugar.

**Joias especiais:**
- ⚡ **Raio** (4 em linha): ao ser destruída, limpa **a linha e a coluna** inteiras.
- 💥 **Bomba** (combinação em **L** ou **T**): explode tudo em volta (3×3).
- 🌟 **Estrela** (5 em linha): **troque com qualquer joia** para apagar **todas daquela cor**!

**Cascatas:** quando as joias que caem formam novas combinações, os pontos se multiplicam (×2, ×3…) e a música sobe de tom. 🎵 Se você ficar parado, uma dica pisca no tabuleiro.
""",
    "🏔️ Voo Alienígena": """
**🎯 Objetivo:** pilotar uma nave pelos **cânions sinuosos** de um planeta alienígena sem bater nas montanhas, voando o mais longe possível.

**Controles:** 🖱️ o **mouse** pilota (para os lados vira, e para cima e para baixo sobe e desce), ou 📱 **arraste o dedo**. No teclado, use as **setas**. Existe um **teto de voo**, então não dá para fugir por cima das montanhas: você tem que seguir o cânion! Um piloto automático leve ajuda nas curvas, e um sensor de solo te empurra para cima quando chega perto demais.

**Pontos:** a distância soma pontos, e cada **💫 anel azul** atravessado vale um combo e dá **mais velocidade**. Você tem **3 vidas 💜**.

*Tecnologia de outro mundo: não existe nenhum modelo 3D aqui. Cada pixel do planeta (montanhas, cristais brilhantes, neblina, sol rosa e as duas luas) é **calculado matematicamente** por **raymarching** num shader que roda na placa de vídeo. O jogo ainda **ajusta a resolução sozinho** para rodar liso no seu aparelho.*
""",
    "9️⃣ Sudoku": """
**🎯 Objetivo:** preencher a grade 9×9 com números de **1 a 9** sem repetir nenhum número na mesma **linha**, na mesma **coluna** ou no mesmo **quadrado 3×3**. Todo Sudoku gerado tem **uma única solução**.

**Como jogar:** clique numa casa vazia e depois num número do teclado (no computador, também dá para digitar de 1 a 9 e andar com as setas). Os números que **você** coloca aparecem em azul, e os que já vieram no jogo, em branco. Um número errado fica vermelho e conta **1 erro**. Com 3 erros, o jogo acaba.

**Ferramentas:**
- ✏️ **Notas:** liga o modo rascunho para anotar os candidatos de uma casa.
- 💡 **Dica:** revela uma casa.
- O número pequeno embaixo de cada botão mostra **quantos daquele número ainda faltam**.

**💡 Estratégia:** procure linhas, colunas ou quadrados que já estejam quase cheios. Pergunte: *"nesta linha falta o 7; em qual casa ele pode entrar?"*. Se só sobrar um lugar possível, o número é ali.
""",
    "🔐 Senha": """
**🎯 Objetivo:** descobrir a **senha secreta de cores** em até **10 tentativas**.

**Como jogar:** clique nas cores da paleta para montar seu palpite (clique numa bolinha do palpite para tirá-la) e aperte **✅ Conferir**. As bolinhas pequenas do lado mostram o resultado:
- ⚫ **Preta:** uma cor certa **no lugar certo**.
- ⚪ **Branca:** uma cor certa, mas **no lugar errado**.

As bolinhas de resposta **não dizem qual cor** é qual. Esse é o desafio! 🧠

**Modos:** *Fácil* tem 4 cores sem repetição. *Normal* tem 4 posições com 6 cores, e as cores podem repetir. *Difícil* tem 5 posições e 8 cores.

**💡 Estratégia:** comece com palpites que testem várias cores, como 🔴🔴🔵🔵, e use cada resposta para eliminar possibilidades.
""",
    "🗼 Torre de Hanói": """
**🎯 Objetivo:** levar **todos os discos** da torre da esquerda para a torre da **direita**.

**Regras:**
1. Você move **um disco por vez**: clique numa torre para pegar o disco de cima e em outra torre para soltá-lo.
2. **Nunca** coloque um disco **maior em cima de um menor**.

O menor número possível de movimentos é **2ⁿ − 1** (com 4 discos, são 15 movimentos). Conseguir esse número é **perfeito ⭐⭐⭐**.

**💡 Segredo:** para mover uma torre de *n* discos, primeiro mova os *n − 1* de cima para a torre do meio, depois mova o maior e, por fim, traga os *n − 1* de volta para cima dele. Travou? O botão **🤖 Ver solução** mostra o caminho perfeito.
""",
    "🧮 Quebra-Cabeça Deslizante": """
**🎯 Objetivo:** colocar as peças **em ordem** (1, 2, 3… da esquerda para a direita, de cima para baixo), deixando o espaço vazio no **canto inferior direito**.

**Como jogar:** clique numa peça que esteja na **mesma linha ou coluna** do espaço vazio, e ela desliza para lá (se houver várias no caminho, todas deslizam juntas). No computador, use as **setas**. As peças que já estão no lugar certo ganham uma borda clara.

**Tamanhos:** 3×3 (fácil), 4×4 (o clássico) e 5×5 (difícil).

**💡 Estratégia:** resolva a **primeira linha**, depois a **primeira coluna**, e assim por diante, reduzindo o problema até sobrar um 2×2.
""",
    "💡 Apague as Luzes": """
**🎯 Objetivo:** **apagar todas as luzes** do tabuleiro.

**A pegadinha:** ao clicar numa casa, ela **e as 4 vizinhas** (acima, abaixo, esquerda e direita) **trocam de estado**: o que estava aceso apaga e o que estava apagado acende.

Cada nível tem uma **meta de cliques**. Resolver dentro da meta vale ⭐⭐⭐. A cada nível o desafio fica maior.

**💡 Truques de quem é bom nisso:**
- Clicar duas vezes na mesma casa desfaz o clique, então a ordem dos cliques **não importa**.
- Técnica de **"arrastar as luzes para baixo"**: para cada luz acesa numa linha, clique na casa **logo abaixo dela**. Faça isso linha por linha até sobrarem luzes só na última linha, e então ajuste a primeira linha conforme o padrão que sobrou.
""",
    "🌌 Galáxia 3D": """
**🎯 Objetivo:** pilotar sua nave pelo espaço em **3D**, destruir asteroides e naves inimigas e sobreviver o máximo de **ondas** possível. A cada 25 segundos vem uma onda nova, mais rápida e com mais inimigos.

**Controles:**
- ⌨️ **Setas** ou **WASD** movem a nave. **ESPAÇO** atira (segure para atirar sem parar).
- 📱 **Arraste o dedo** na tela para pilotar. Enquanto o dedo estiver na tela, a nave **atira sozinha**.

**Pontos:** 🪨 asteroide = 50 e 🔺 nave inimiga = 200, multiplicados pelo número da onda. As naves vermelhas **atiram em você**! Asteroides grandes aguentam 2 tiros, e as naves, 3.

**Itens:** 💚 anel verde dá **tiro triplo** por 9 segundos, e 💙 anel azul dá **+1 escudo**. Você começa com 3 escudos 🛡️ e fica uns instantes invencível depois de levar um golpe.

*Tecnologia: gráficos 3D em tempo real (WebGL), campo com 2.000 estrelas, explosões de partículas, luzes dinâmicas e sons sintetizados na hora.*
""",
    "🏙️ Corrida Infinita 3D": """
**🎯 Objetivo:** correr **o mais longe possível** pela cidade neon em 3D sem bater. A velocidade aumenta o tempo todo!

**Controles:**
- ⬅️ ➡️ **mudam de pista** (são 3 pistas).
- ⬆️ ou **ESPAÇO** **pulam** as barreiras 🟥 **vermelhas e baixas**.
- ⬇️ faz **deslizar por baixo** das barras 🟧 **laranjas e altas**.
- 🟪 **Muros roxos** não dá para pular nem deslizar: só **mudando de pista**.
- 📱 No celular, **deslize o dedo** para os lados, para cima ou para baixo, ou use os botões. Um toque rápido também pula.

**Pontos:** a distância em metros é a sua pontuação, e as 🪙 **moedas** contam à parte. Bateu, acabou!

*Tecnologia: cenário 3D infinito gerado na hora (WebGL), robô animado, prédios com contorno neon, neblina e câmera que segue você.*
""",
    "🧩 Labirinto 3D": """
**🎯 Objetivo:** **inclinar o tabuleiro** para fazer a **bola de metal** rolar até o **círculo verde** que brilha no canto. Cada nível gera um labirinto **novo e maior**.

**Controles:**
- ⌨️ **Setas** ou **WASD** inclinam o tabuleiro.
- 📱 **Arraste o dedo** na direção em que quer inclinar (a partir de onde você tocou).
- 📱 **Giroscópio:** toque em *"Usar giroscópio do celular"* e incline o **próprio celular**! (Alguns navegadores bloqueiam isso dentro de sites; se acontecer, use o dedo.)

A bola tem **física de verdade**: ela ganha velocidade, quica nas paredes e não para na hora. Vá com calma nas curvas! ⭐⭐⭐ é para quem termina rápido.

*Tecnologia: física com colisões, sombras em tempo real, centenas de paredes desenhadas de uma vez (instancing) e suporte a giroscópio.*
""",
    "🧱 Quebra-Blocos Neon": """
**🎯 Objetivo:** rebater a bola com a raquete e **destruir todos os blocos** de cada nível sem deixar a bola cair.

**Controles:** 🖱️ mova o **mouse** ou o **dedo** sobre o jogo (ou use ← →). **ESPAÇO**, clique ou toque **lançam** a bola. **P** pausa.

**Dica de mira:** se a bola bater na **ponta** da raquete, ela sai inclinada. Se bater **no meio**, sai reta.

**Blocos especiais:**
- Blocos mais claros aguentam **mais de um golpe**.
- 🔩 **Metal** (cinza) aguenta 4 golpes.
- ✸ **Bomba** (laranja) **explode os vizinhos**!

**Cápsulas que caem:** **M** multibola · **L** raquete larga · **T** laser automático · **S** câmera lenta · **V** vida extra.

**Combo:** cada bloco quebrado em sequência, sem a bola voltar à raquete, multiplica os pontos (até ×10)!
""",
    "🟪 Blocos Caindo": """
**🎯 Objetivo:** encaixar as peças que caem e **completar linhas inteiras**, que somem e dão pontos. Se as peças chegarem ao topo, acabou!

**Controles:**
- ⬅️ ➡️ movem a peça (segure para deslizar).
- ⬆️ ou **X** giram, e **Z** gira ao contrário.
- ⬇️ desce mais rápido. **ESPAÇO** **larga** a peça de uma vez.
- **C** **guarda** a peça para usar depois (uma vez por peça). **P** pausa.
- 📱 Botões: ◀ ⟳ ▼ ⤓ (largar) ⇄ (guardar) ▶.

O contorno **fantasma** mostra onde a peça vai cair, e o painel mostra as **3 próximas peças**.

**Pontos:** 1 linha = 100, 2 = 300, 3 = 500 e **4 de uma vez = 800**, tudo vezes o nível. A cada 10 linhas, sobe de nível e fica mais rápido.

**💡 Estratégia:** deixe uma coluna livre na lateral e espere a peça comprida para fazer **4 linhas de uma vez**.
""",
    "👑 A Vida É um Jogo": """
**🎯 Objetivo:** sair do zero (R$ 3.000 e um computador velho) e construir um **império**, sem perder o que mais importa no caminho. A vitória não é só dinheiro. Sua **pontuação de vida** (0 a 1000) mede **5 dimensões**: 💰 Prosperidade · 🏢 Empresa · 🌿 Qualidade de vida · 🤝 Relacionamentos · ⚖️ Integridade.

**Como cada mês funciona:**
1. **Escolha onde colocar sua energia:** vender, marketing, estudar, networking, descansar, inovar ou mudar para uma estrutura maior.
2. **Viva um acontecimento:** sócios, amigos, amores, fiscais, golpes, crises, propostas milionárias… Escolha o que fazer.
3. **Veja o fechamento do mês:** lucro ou prejuízo, notícias e conquistas. A 🔮 prévia mostra o que vem no próximo mês.

**⚠️ Consequências demoram:** muitas decisões só mostram o resultado **meses depois**. Confiar em quem não devia pode custar caro lá na frente.

**👥 Pessoas:** cada pessoa tem um **caráter secreto** (pode ser confiável ou não). Investigue, observe as atitudes e **converse com elas** na aba *Pessoas*. A IA dá vida a cada personagem, e os desonestos deixam pistas sutis.

**💼 Gestão:**
- **Equipe:** quando a demanda passa da sua capacidade, contrate. Cliente sem atendimento derruba a reputação.
- **Estrutura:** limita quantos funcionários cabem. Mude para um espaço maior para crescer.
- **Banco:** empréstimo a 3,5% ao mês. Se o caixa ficar negativo, o banco cobre com **cheque especial a 8%**. Se nem isso der, é **falência**.
- **Saúde emocional:** se zerar, você tem um *burnout*. Descanse!

**❤️ Vida afetiva:** namoro e casamento trazem felicidade **se você estiver presente**. A *atenção ao relacionamento* cai todo mês (mais rápido depois do casamento) e sobe quando você escolhe **🧘 Cuidar de você e da família**. Abandonado, o amor esfria, e pode vir até uma traição 💔. Um 👶 **filho** muda suas prioridades: mais alegria, mais custo e dilemas entre a família e o trabalho.

**🏆 Fases:** 🌱 Sonhador → 🛠️ Autônomo → 🏪 Pequeno Negócio → 🏢 Em Crescimento → 🏙️ Consolidada → 🏰 **Império**. São 21 conquistas para desbloquear, e no mês 60 tem uma avaliação dos seus 5 anos.

**🧬 Legado:** cada vida que termina vai para o **Hall da Fama** e te dá **conhecimento extra** na próxima. Quanto mais você joga, mais longe vai.

**💡 Dicas:** comece no ramo de **serviços** ou **imobiliário** (os mais fáceis). Não gaste todo o caixa de uma vez. Contrate quando faltar capacidade. E desconfie de quem promete demais e tem pressa.
""",
    "🪩 Pinball": """
**🎯 Objetivo:** fazer o máximo de pontos **sem deixar a bola cair** no buraco entre as duas palhetas amarelas. Você tem **3 bolas**.

**Controles:**
- **Lançar a bola:** segure **ESPAÇO** (ou o botão 🚀) para puxar a mola e solte. Quanto mais tempo segurar, mais forte vai.
- **Palheta esquerda:** **←** ou **A** (no celular, toque no lado esquerdo da tela ou em "◀ Palheta").
- **Palheta direita:** **→** ou **D** (no celular, toque no lado direito ou em "Palheta ▶").
- **P** pausa o jogo.

**Pontos:**
- 🔴🟢🟠 **Bumpers** (círculos coloridos) arremessam a bola e valem **100**.
- 🩷 **Estilingues** (linhas rosa acima das palhetas) chutam a bola e valem **10**.
- 💡 Acenda as **3 luzes do topo** passando por elas para ganhar **+500** e aumentar o **multiplicador** (até x5). Ele multiplica todos os pontos!

**💡 Dica:** não fique apertando sem parar. Espere a bola chegar perto da palheta e bata no momento certo, porque a ponta da palheta joga a bola mais longe.
""",
    "🟢 Come-Come": """
**🎯 Objetivo:** você é o **slime verde 🟢**. Coma **todas as bolinhas** do labirinto sem ser pego pelos **vírus**. Ao limpar o labirinto, você passa de nível, e a cada nível os vírus ficam mais rápidos. Você tem **3 vidas**.

**Controles:** **setas** ou **W A S D** no teclado. No celular, **arraste o dedo** na direção que quer ir ou use os botões ◀ ▲ ▼ ▶. Dá para apertar a direção **antes** de chegar na curva, e o slime vira assim que der. **P** pausa.

**Pontos:**
- Bolinha pequena: **10**
- ⚪ **Bolona** (nos cantos): **50**, e os vírus ficam **azuis e com medo** por alguns segundos. Nesse tempo **você pode comê-los**! Eles valem 200, 400, 800... em sequência. Quando começam a **piscar**, o efeito está acabando.

**💡 Dicas:**
- Os corredores das laterais do meio são um **túnel**: sai de um lado e aparece do outro.
- Guarde as bolonas para quando os vírus estiverem perto de você.
- Cada vírus tem um jeito: o vermelho persegue você direto, o laranja tenta cortar sua frente e o roxo às vezes desiste e vai para o canto.
""",
    "🏎️ Corrida": """
**🎯 Objetivo:** dirigir o carro vermelho o **mais longe possível**, desviando dos outros carros. A velocidade vai **aumentando** com o tempo!

**Controles:** **←** e **→** (ou **A** e **D**). No celular, **segure o dedo** no lado esquerdo ou direito da tela, ou use os botões. **P** pausa.

**Pontos e vidas:**
- Os pontos sobem conforme a distância percorrida.
- 🪙 **Moeda** dourada vale **+50**.
- Você tem **3 vidas ❤️**. A cada batida perde uma, e o carro fica piscando por 2 segundos (nesse tempo não bate de novo).

**💡 Dica:** não fique colado num lado da pista. Fique perto do meio para conseguir fugir para qualquer lado, e olhe sempre lá na frente.
""",
    "♟️ Xadrez": COMO_XADREZ,
    "🔢 Adivinhe o Número": """
**🎯 Objetivo:** descobrir o número secreto que o computador pensou usando o **menor número de chutes**.

**Como jogar:** escolha a dificuldade, digite um número e clique em **Chutar**. O jogo diz se o número secreto é **maior ⬆️** ou **menor ⬇️** que o seu chute.

**💡 Dica:** chute sempre **no meio** do intervalo que sobrou. Por exemplo, de 1 a 100 chute 50; se for maior, chute 75; e assim por diante. Com essa estratégia você acerta qualquer número de 1 a 100 em no máximo 7 chutes!
""",
    "❌⭕ Jogo da Velha": """
**🎯 Objetivo:** fazer uma **linha de 3** com o seu símbolo, na horizontal, na vertical ou na diagonal.

**Como jogar:** você é o **❌** e sempre começa. Clique numa casa vazia, e o computador (**⭕**) joga logo depois. Se as 9 casas encherem sem ninguém fazer linha, **deu velha** (empate).

**Níveis:** *Fácil* joga aleatório, *Médio* às vezes erra e *Impossível* nunca perde (o melhor que dá é empatar).

**💡 Dicas:** comece pelo **centro** ou por um **canto**. Sempre bloqueie quando o adversário tiver 2 em linha. Tente criar duas ameaças ao mesmo tempo para ele não conseguir bloquear as duas.
""",
    "🪢 Forca": """
**🎯 Objetivo:** descobrir a palavra secreta **antes que o boneco seja enforcado**.

**Como jogar:** veja a **dica** (a categoria da palavra) e clique nas letras. Se a letra existir na palavra, ela aparece em todos os lugares onde estiver. Se não existir, uma parte do boneco é desenhada. Com **6 erros**, você perde.

**💡 Dicas:** comece pelas **vogais** (A, E, O, I) e depois tente as consoantes mais comuns em português: R, S, M, N, T, C. As palavras não têm acento.
""",
    "🪨 Pedra, Papel e Tesoura": """
**🎯 Objetivo:** escolher o objeto que **ganha** do objeto do computador.

**Quem ganha de quem:**
- 🪨 **Pedra** quebra a ✂️ **Tesoura**
- ✂️ **Tesoura** corta o 📄 **Papel**
- 📄 **Papel** embrulha a 🪨 **Pedra**

Se os dois escolherem a mesma coisa, é **empate**. Clique na sua escolha, e o computador escolhe ao mesmo tempo, sem trapaça. O placar vai somando.
""",
    "🧠 Jogo da Memória": """
**🎯 Objetivo:** encontrar todos os **8 pares** de bichinhos usando o menor número de jogadas.

**Como jogar:** clique em uma carta ❓ para virá-la e depois em outra.
- Se as duas forem **iguais**, elas ficam abertas. ✅
- Se forem **diferentes**, elas ficam à mostra até você clicar na próxima carta e depois se escondem de novo. Tente **lembrar onde estava cada bicho**!

Cada par de cartas viradas conta como **1 jogada**. O mínimo possível é 8.
""",
    "🟩 Termo": """
**🎯 Objetivo:** adivinhar a **palavra secreta de 5 letras** em até **6 tentativas**.

**Como jogar:** digite qualquer palavra de 5 letras e clique em **Enviar**. Cada letra muda de cor:
- 🟩 **Verde:** a letra está na palavra e **no lugar certo**.
- 🟨 **Amarelo:** a letra está na palavra, mas **em outro lugar**.
- ⬛ **Cinza:** a letra **não está** na palavra.

O teclado embaixo mostra as letras que você já testou. Não precisa usar acento (AVIÃO = AVIAO).

**💡 Dica:** no primeiro chute use uma palavra com várias vogais diferentes, como **AUDIO** ou **TEIAS**.
""",
    "🔢 2048": """
**🎯 Objetivo:** juntar os números até formar um bloco com **2048**.

**Como jogar:** use as setas ⬅️ ⬆️ ⬇️ ➡️. **Todos** os blocos deslizam para aquele lado ao mesmo tempo. Quando dois blocos com o **mesmo número** se encostam, eles se **somam** e viram um só (2+2=4, 4+4=8, 8+8=16...). A cada movimento aparece um bloco novo (2 ou 4) num espaço vazio.

O jogo acaba quando o tabuleiro enche e não há mais nenhuma soma possível. Cada soma vale pontos.

**💡 Dicas:** escolha um **canto** para guardar o maior número e não tire ele de lá. Use quase sempre só 2 ou 3 direções (por exemplo ⬇️ e ⬅️, e às vezes ➡️) e evite a direção que tira o bloco grande do canto.
""",
    "💣 Campo Minado": """
**🎯 Objetivo:** abrir **todas as casas sem mina**, sem pisar em nenhuma bomba.

**Como jogar:**
- Com o modo **⛏️ Abrir** selecionado, clique numa casa para abri-la. O **primeiro clique nunca é mina**.
- O **número** numa casa aberta diz **quantas minas existem nas 8 casas em volta** dela (lados e diagonais).
- Casa vazia significa zero minas em volta, e o jogo abre a região sozinho.
- Troque para **🚩 Bandeira** para marcar onde você acha que tem mina. Clique de novo para tirar a marcação. Casas com bandeira não abrem por acidente.

**💡 Dica:** se uma casa com **1** só tem **uma** casa fechada em volta, essa casa é mina. Marque com bandeira. Se um número já tem todas as suas minas marcadas, as outras casas em volta dele são **seguras**.
""",
    "🔴 Ligue 4": """
**🎯 Objetivo:** ser o primeiro a **alinhar 4 peças** da sua cor na horizontal, na vertical ou na diagonal.

**Como jogar:** você é o **🔴** e começa. Clique em **qualquer casa de uma coluna** e sua peça **cai** até o fundo dessa coluna, parando na primeira casa livre. Depois o computador (**🟡**) joga. Se o tabuleiro encher sem ninguém fazer 4, é empate.

**💡 Dicas:** jogue pelo **meio**, porque a coluna central participa de mais linhas. Sempre olhe se o computador tem **3 em linha** e bloqueie. Tente montar duas ameaças ao mesmo tempo.
""",
    "🤖 Quiz com IA": """
**🎯 Objetivo:** acertar o máximo de perguntas de um quiz **criado na hora pela inteligência artificial** (usando a sua chave Groq).

**Como jogar:**
1. Escreva **qualquer tema** (futebol, história, filmes, ciências, sua série favorita...).
2. Escolha a dificuldade e quantas perguntas quer, e clique em **✨ Gerar quiz**.
3. Para cada pergunta, marque uma opção e clique em **Responder**. Você vê na hora se acertou e uma explicação.
4. No final aparece a sua pontuação.

⚠️ A IA pode errar de vez em quando. Se uma resposta parecer estranha, confira em outra fonte.
""",
}


# =====================================================================
# MENU
# =====================================================================
CATEGORIAS = {
    "⭐ Destaque": {
        "👑 A Vida É um Jogo": jogo_vida,
        "⚽ Copa de Futsal": jogo_futsal,
    },
    "✨ De Outro Mundo": {
        "🏔️ Voo Alienígena": lambda: jogo_mundo("voo"),
        "🌀 Portal Cósmico": lambda: jogo_mundo("portal"),
        "🎹 Sinfonia das Estrelas": lambda: jogo_mundo("sinfonia"),
        "🪐 Estilingue Cósmico": lambda: jogo_mundo("estilingue"),
        "💎 Joias Encantadas": lambda: jogo_mundo("joias"),
    },
    "🚀 3D e Ação": {
        "🌌 Galáxia 3D": lambda: jogo_tech("galaxia"),
        "🏙️ Corrida Infinita 3D": lambda: jogo_tech("runner"),
        "🧩 Labirinto 3D": lambda: jogo_tech("labirinto"),
        "🧱 Quebra-Blocos Neon": lambda: jogo_tech("quebra"),
        "🟪 Blocos Caindo": lambda: jogo_tech("caindo"),
        "🪩 Pinball": jogo_pinball,
        "🟢 Come-Come": jogo_comecome,
        "🏎️ Corrida": jogo_corrida,
    },
    "🧠 Raciocínio": {
        "♟️ Xadrez": jogo_xadrez,
        "9️⃣ Sudoku": lambda: jogo_raciocinio("sudoku"),
        "🔐 Senha": lambda: jogo_raciocinio("senha"),
        "🗼 Torre de Hanói": lambda: jogo_raciocinio("hanoi"),
        "🧮 Quebra-Cabeça Deslizante": lambda: jogo_raciocinio("desliza"),
        "💡 Apague as Luzes": lambda: jogo_raciocinio("luzes"),
        "🟩 Termo": jogo_termo,
        "💣 Campo Minado": jogo_campo_minado,
        "🔢 2048": jogo_2048,
    },
    "🤖 Com IA": {
        "🤖 Quiz com IA": jogo_quiz_ia,
    },
    "🎲 Clássicos": {
        "🔴 Ligue 4": jogo_ligue4,
        "❌⭕ Jogo da Velha": jogo_velha,
        "🧠 Jogo da Memória": jogo_memoria,
        "🪢 Forca": jogo_forca,
        "🔢 Adivinhe o Número": jogo_adivinha,
        "🪨 Pedra, Papel e Tesoura": jogo_ppt,
    },
}
JOGOS = {nome: fn for cat in CATEGORIAS.values() for nome, fn in cat.items()}


# =====================================================================
# TELA DE ENTRADA (nome + chave Groq)
# =====================================================================
MODELOS_PREFERIDOS = ["llama-3.3-70b-versatile", "openai/gpt-oss-120b", "openai/gpt-oss-20b",
                      "llama-3.1-8b-instant"]


def escolher_modelo(ids):
    for m in MODELOS_PREFERIDOS:
        if m in ids:
            return m
    texto = [m for m in ids if not any(x in m for x in ("whisper", "tts", "guard", "playai", "vision"))]
    return (texto or ids or ["llama-3.3-70b-versatile"])[0]


def validar_chave_groq(chave: str):
    """Retorna (ok, mensagem, lista_de_modelos)."""
    try:
        r = requests.get("https://api.groq.com/openai/v1/models",
                         headers={"Authorization": f"Bearer {chave}"}, timeout=10)
    except requests.RequestException:
        return False, "Não consegui falar com a Groq agora. Tente de novo em instantes.", []
    if r.status_code == 200:
        return True, "", [m.get("id", "") for m in r.json().get("data", [])]
    if r.status_code in (401, 403):
        return False, "Chave Groq inválida. Confira e tente de novo.", []
    return False, f"A Groq respondeu com erro {r.status_code}. Tente de novo.", []


def tela_entrada():
    st.markdown("<h1 style='text-align:center'>🎮 Fliperama</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align:center'>{len(JOGOS)} jogos para você se divertir. "
                "Digite seu nome e sua chave Groq para entrar.</p>", unsafe_allow_html=True)
    _, meio, _ = st.columns([1, 2, 1])
    with meio, st.form("entrada"):
        nome = st.text_input("Seu nome", max_chars=30)
        chave = st.text_input("Chave Groq", type="password", placeholder="gsk_...",
                              help="Crie a sua grátis em console.groq.com/keys. "
                                   "Ela fica só nesta sessão e não é salva.")
        if st.form_submit_button("Entrar ▶️", type="primary"):
            nome, chave = nome.strip(), chave.strip()
            if not nome or not chave:
                st.error("Preencha o nome e a chave.")
            else:
                with st.spinner("Verificando a chave..."):
                    ok, erro, modelos = validar_chave_groq(chave)
                if ok:
                    S.usuario, S.groq_key, S.groq_modelo = nome, chave, escolher_modelo(modelos)
                    st.rerun()
                else:
                    st.error(erro)


def sair():
    for k in list(S.keys()):
        del S[k]


if "usuario" not in S:
    tela_entrada()
    st.stop()

st.sidebar.title("🎮 Fliperama")
st.sidebar.write(f"Olá, **{S.usuario}**! 👋")
categoria = st.sidebar.radio("Categoria", list(CATEGORIAS), key="menu_categoria")
escolhido = st.sidebar.radio("Escolha um jogo", list(CATEGORIAS[categoria]), key=f"menu_jogo_{categoria}")
st.sidebar.button("🚪 Sair", on_click=sair)
st.sidebar.caption(f"{len(JOGOS)} jogos · feito com Streamlit · um único arquivo .py")

st.header(escolhido)
abrir = ((escolhido == "♟️ Xadrez" and not S.get("xq_board", chess.Board()).move_stack)
         or (escolhido == "👑 A Vida É um Jogo" and not S.get("vida")))
with st.expander("📖 Como jogar", expanded=abrir):
    st.markdown(INSTRUCOES[escolhido])

JOGOS[escolhido]()
