# extração dos dados do arquivo de entrada,
# criação do esquema do banco de dados
# e povoamento das relações com estes dados

import subprocess
import psycopg2
import sys

def fixquote(s):
    l = []
    for c in s:
        if c != "'":
            l.append(c)
        else:
            l.append("''")
    return "".join(l)

esquema = [
"""CREATE TABLE PRODUTO(
ASIN VARCHAR(10) PRIMARY KEY,
ID_PRODUTO BIGINT,
TITULO VARCHAR(500),
GRUPO VARCHAR(20),
avaliacao_media FLOAT,
RANKING BIGINT
); """,
"""CREATE TABLE SIMILAR_PRODUTO(
SIMILAR_ID SERIAL PRIMARY KEY,
ASIN1_FK VARCHAR(10),
ASIN2 VARCHAR(10),
foreign key (ASIN1_FK) references PRODUTO (ASIN)
); """,
"""CREATE TABLE CATEGORIA(
CATEGORIA_ID BIGINT PRIMARY KEY,
CATEGORIA_ID_PAI BIGINT,
NOME VARCHAR(300),
foreign key (CATEGORIA_ID_PAI) references CATEGORIA (CATEGORIA_ID)
); """,
"""CREATE TABLE RELACAO_PRODUTO_CATEGORIA(
RELACAO_ID SERIAL PRIMARY KEY,
CATEGORIA_ID_FK BIGINT,
ASIN_FK VARCHAR(10),
foreign key (CATEGORIA_ID_FK) references CATEGORIA (CATEGORIA_ID),
foreign key (ASIN_FK) references PRODUTO (ASIN)
); """,
"""CREATE TABLE REVIEW(
data_review DATE,
REVIEW_ID SERIAL PRIMARY KEY,
ASIN_FK VARCHAR(10),
AVALIACAO  FLOAT,
VOTOS INT,
UTILIDADE INT,
id_cliente VARCHAR(30),
foreign key (ASIN_FK) references PRODUTO (ASIN)
 ); """
]


# deleta banco de dados se ja existir
print("Deletando banco de dados (caso ja tenha sido criado)")
print("Caso o banco de dados nao exista, um erro sera reportado.")
print("Esse erro nao afeta o funcionamento do programa.")
r = subprocess.run("psql -h localhost -U postgres postgres -c \"DROP DATABASE tp1;\"",
                   shell = True)

# cria banco de dados
print("Criando novo banco de dados tp1")
r = subprocess.run("createdb tp1 -O postgres -h localhost -U postgres",
                   shell = True)
if r.returncode == 0:
    print("Banco de dados criado com sucesso")
else:
    print("Nao foi possivel criar o banco de dados. Tente novamente.")
    sys.exit(1)

conn = psycopg2.connect("dbname=tp1 user=postgres host=localhost password=postgres")

# cria esquema do bd
print("Criando esquema do bd")
cur = conn.cursor()
for table in esquema:
    cur.execute(table)
cur.close()
conn.commit()
print("Esquema do bd criado")

# adiciona elementos do arquivo
amazon_meta = sys.argv[1] if len(sys.argv) > 1 else 'amazon-meta.txt'

try:
    f = open(amazon_meta, 'r', encoding="utf-8")
except FileNotFoundError as e:
    print("amazon-meta.txt not found", file=sys.stderr)
    print("Please add the file to this folder or specify the location", file=sys.stderr)
    print(f"Usage:  python {sys.argv[0]} amazon-meta-file", file=sys.stderr)
    sys.exit(1)
fsimilar = open('.similar.txt', 'w', encoding="utf-8")
fcategorias = open('.categorias.txt', 'w', encoding="utf-8")
freview = open('.review.txt', 'w', encoding="utf-8")

categorias = dict()

cur = conn.cursor()
print("Lendo arquivo de entrada")

line = f.readline()
line = f.readline()
itnum = int(line.split()[2])
itcnt = 0

while True:
    try:
        line = f.readline()
    except EOFError:
        break

    if len(line) == 0:
        continue

    if line[:3] != "Id:":
        continue

    id = int(line[6:-1])
    itcnt += 1

    line = f.readline()
    asin = line[6:-1]
    #if id % 1000 == 0:
    #    print(id)

    line = f.readline()
    l = line[2:-1]
    if l == "discontinued product":
        sql = f"INSERT INTO produto(asin, id_produto) VALUES('{asin}', {id});"
        cur.execute(sql)
        continue
    title = fixquote(l[7:])

    line = f.readline()
    group = fixquote(line[9:-1])

    line = f.readline()
    rank = int(line[12:-1])


    #similar
    line = f.readline().split()
    l = line[2:]
    for item in l:
        print(asin, item, file=fsimilar)

    #categories
    line = f.readline().split()
    catnum = int(line[1])
    for i in range(catnum):
        line = f.readline()[4:-1].split('|')
        pai = "NULL"
        for cat in line:
            for i in range(len(cat)):
                if cat[i] == '[':
                    catn = i
            cats = fixquote(cat[:catn])
            catn = int(cat[catn+1:-1])
            if not catn in categorias:
                categorias[catn] = [cats, pai]
            pai = catn

        print(pai, asin, file=fcategorias)


    #reviews
    line = f.readline().split()
    revnum = int(line[4])
    avgrating = float(line[7])

    for i in range(revnum):
        line = f.readline().split()
        date = line[0]
        cliente = line[2]
        rating = float(line[4])
        votes = int(line[6])
        helpful = int(line[8])

        print(date, asin, rating, votes, helpful, cliente, file=freview)



    sql = "INSERT INTO produto(asin, id_produto, titulo, grupo, ranking, avaliacao_media) " + \
         f"VALUES('{asin}', {id}, '{title}', '{group}', {rank}, {avgrating});"
    cur.execute(sql)

    if itcnt >= itnum:
        break

cur.close()
conn.commit()

print("Arquivo lido com sucesso")

f.close()
fsimilar.close()
fcategorias.close()
freview.close()

print("Preenchendo tabela categorias")
cur = conn.cursor()
for cat in categorias:
    x = categorias[cat]
    sql = "INSERT INTO categoria(categoria_id, categoria_id_pai, nome) " + \
          f"VALUES({cat}, {x[1]}, '{x[0]}');"
    cur.execute(sql)
cur.close()
conn.commit()
print("Tabela categorias preenchida")

print("Preenchendo tabela similar")
cur = conn.cursor()
fsimilar = open('.similar.txt', 'r', encoding="utf-8")
for line in fsimilar:
    asin, item = line.split()
    sql = "INSERT INTO similar_produto(asin1_fk, asin2) " + \
         f"VALUES('{asin}', '{item}');"
    cur.execute(sql)
fsimilar.close()
print("Tabela similar preenchida")

cur.close()
conn.commit()

print("Preenchendo tabela relacao_produto_categoria")
cur = conn.cursor()
fcategorias = open('.categorias.txt', 'r', encoding="utf-8")
for line in fcategorias:
    cat, asin = line.split()
    sql = "INSERT INTO relacao_produto_categoria(categoria_id_fk, asin_fk) " + \
         f"VALUES({cat}, '{asin}');"
    cur.execute(sql)
fcategorias.close()
cur.close()
conn.commit()
print("Tabela relacao_produto_categoria preenchida")

print("Preenchendo tabela review")
cur = conn.cursor()
freview = open('.review.txt', 'r', encoding="utf-8")
for line in freview:
    date, asin, rating, votes, helpful, cliente = line.split()
    sql = "INSERT INTO review(data_review, asin_fk, avaliacao, votos, utilidade, id_cliente) " + \
         f"VALUES('{date}', '{asin}', {rating}, {votes}, {helpful}, '{cliente}');"
    cur.execute(sql)
freview.close()
cur.close()
conn.commit()
print("Tabela review preenchida")


conn.close()

print("Banco de dados tp1 criado e preenchido com sucesso")
