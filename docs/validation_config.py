# =============================================================================
# CONFIGURAÇÕES DE VALIDAÇÃO - APARATOS LEGAIS BRASILEIROS
# =============================================================================
# Baseado em: Marco Civil da Internet (Lei 12.965/2014), LGPD (Lei 13.709/2018),
# Código Penal, Estatuto da Criança e do Adolescente, Lei de Crimes Cibernéticos

# **Configurações de validação**
VALIDATION_ENABLE_PROFANITY_FILTER = True

# PALAVRAS PROIBIDAS - Baseadas na legislação penal e civil brasileira
VALIDATION_FORBIDDEN_WORDS = """
# Crimes contra a honra (Art. 138-140 CP)
difamacao, calonia, injuria, mentiroso, ladrao, corrupto,

# Discriminação racial (Lei 7.716/89)
macaco, pretinho, nego, crioulo, mulato,

# Discriminação religiosa (Art. 208 CP)
macumbeiro, demonio, seita, herege,

# Crimes sexuais e pedofilia (Art. 213-218 CP, ECA)
pedofilo, estupro, molestador, abuso_sexual, exploração_sexual,

# Ameaças e violência (Art. 147 CP)
matar, assassinar, explodir, bomba, atentado, terrorismo,

# Drogas ilícitas (Lei 11.343/06)
cocaina, maconha, crack, heroina, trafico_drogas,

# Fraudes e golpes (Art. 171 CP)
golpe, fraude, esquema_piramide, lavagem_dinheiro,

# Discurso de ódio (Art. 140 §3º CP)
nazista, fascista, xenofobia, homofobia,

# Crimes cibernéticos (Lei 12.737/12)
hacker, invasao_sistema, phishing, malware, ransomware,

# Jogos ilegais (Lei das Contravenções Penais)
jogo_bicho, apostas_ilegais, cassino_clandestino,

# Violência doméstica (Lei Maria da Penha)
bater_mulher, violencia_domestica, espancamento,

# Exploração do trabalho (CLT, Art. 149 CP)
trabalho_escravo, exploração_infantil, mao_obra_escrava
"""

# DOMÍNIOS PERMITIDOS - Instituições governamentais e certificadas
VALIDATION_ALLOWED_DOMAINS = """
# Governo Federal
gov.br, planalto.gov.br, receita.fazenda.gov.br, bcb.gov.br, anatel.gov.br,

# Sistema Judiciário
stf.jus.br, stj.jus.br, cnj.jus.br, tjsp.jus.br, tjrj.jus.br,

# Órgãos de controle
tcu.gov.br, cgu.gov.br, mpf.mp.br, defensoria.gov.br,

# Educação e pesquisa
mec.gov.br, capes.gov.br, cnpq.br, inep.gov.br,

# Saúde
saude.gov.br, anvisa.gov.br, fiocruz.br, sus.gov.br,

# Segurança pública
pf.gov.br, dpf.gov.br, ssp.sp.gov.br,

# Bancos oficiais
bb.com.br, caixa.gov.br, bndes.gov.br,

# Universidades públicas
usp.br, unicamp.br, ufrj.br, ufmg.br, unb.br,

# Organizações certificadas
oab.org.br, cfc.org.br, crea.org.br, crc.org.br
"""

VALIDATION_BUSINESS_HOURS_ONLY = False

# **Configurações de domínios permitidos para empresas**
ENTERPRISE_ALLOWED_DOMAINS = """
# Grandes corporações verificadas
petrobras.com.br, vale.com, itau.com.br, bradesco.com.br,
ambev.com.br, jbs.com.br, embraer.com.br,

# Tecnologia
microsoft.com, google.com, amazon.com, ibm.com,
oracle.com, salesforce.com, adobe.com,

# Telecomunicações
vivo.com.br, tim.com.br, claro.com.br, oi.com.br,

# Energia
eletrobras.com, light.com.br, cpfl.com.br,

# Varejo
magazineluiza.com.br, americanas.com.br, carrefour.com.br
"""

# PALAVRAS PROIBIDAS PARA EMPRESAS - Termos que violam compliance
ENTERPRISE_FORBIDDEN_WORDS = """
# Violações trabalhistas (CLT)
trabalho_escravo, exploração_trabalhador, sem_carteira,
salario_atrasado, hora_extra_nao_paga, assedio_moral,

# Crimes ambientais (Lei 9.605/98)
poluicao_ilegal, desmatamento_ilegal, crime_ambiental,
descarte_toxico, vazamento_quimico,

# Corrupção (Lei 12.846/13 - Lei Anticorrupção)
propina, suborno, corrupção, caixa_dois, lavagem_dinheiro,
cartel, licitação_fraudada, lobby_ilegal,

# Violações fiscais
sonegacao, evasao_fiscal, nota_fria, imposto_sonegado,

# Crimes contra consumidor (CDC)
propaganda_enganosa, venda_casada, abusividade,
produto_defeituoso_oculto, garantia_negada,

# Violações de privacidade (LGPD)
venda_dados_pessoais, vazamento_dados, uso_indevido_dados,
coleta_sem_consentimento, perfil_discriminatorio,

# Práticas anticompetitivas (Lei 12.529/11)
monopolio, dumping, concorrencia_desleal,

# Discriminação no trabalho
discriminacao_racial, discriminacao_genero, discriminacao_idade,
discriminacao_religiao, assedio_sexual,

# Segurança e saúde do trabalho
negligencia_seguranca, acidente_trabalho_ocultado,
equipamento_seguranca_negado
"""

# CONFIGURAÇÕES FINAIS
ALLOWED_DOMAINS = VALIDATION_ALLOWED_DOMAINS + "," + ENTERPRISE_ALLOWED_DOMAINS
ENTERPRISE_FORBIDDEN_WORDS = VALIDATION_FORBIDDEN_WORDS + "," + ENTERPRISE_FORBIDDEN_WORDS

# =============================================================================
# REFERÊNCIAS LEGAIS
# =============================================================================
"""
PRINCIPAIS APARATOS LEGAIS CONSULTADOS:

1. Lei 12.965/2014 - Marco Civil da Internet
2. Lei 13.709/2018 - Lei Geral de Proteção de Dados (LGPD)
3. Código Penal Brasileiro (Decreto-Lei 2.848/1940)
4. Lei 8.078/1990 - Código de Defesa do Consumidor
5. Lei 7.716/1989 - Crimes de Preconceito e Discriminação
6. Lei 11.340/2006 - Lei Maria da Penha
7. Lei 8.069/1990 - Estatuto da Criança e do Adolescente
8. Lei 12.737/2012 - Lei Carolina Dieckmann (Crimes Cibernéticos)
9. Lei 12.846/2013 - Lei Anticorrupção
10. Lei 12.529/2011 - Lei de Defesa da Concorrência
11. Consolidação das Leis do Trabalho (CLT)
12. Lei 9.605/1998 - Lei de Crimes Ambientais

OBSERVAÇÕES IMPORTANTES:
- As listas devem ser atualizadas periodicamente conforme mudanças legislativas
- Implementar logs de auditoria para monitoramento do sistema
- Considerar graduação de severidade para diferentes tipos de violações
- Manter processo de revisão jurídica regular das configurações
"""