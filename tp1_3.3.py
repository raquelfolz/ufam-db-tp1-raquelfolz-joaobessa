# dashboard

import subprocess


helpstring = """
-? a asin       | Exibe os 10 comentarios mais uteis no produto [asin].
                  Os 5 primeiros têm a maior avaliação e os 5 últimos têm a menor.

-? b asin       | Lista os produtos similares ao produto [asin] que são mais vendidos que ele.

-? c asin       | Exibe a evolução por dia da média de avaliações do produto [asin].

-? d            | Lista os 10 produtos mais vendidos de cada grupo.

-? e            | Lista os 10 produtos com maior média de avaliações úteis positivas.

-? f            | Lista as 5 categorias com maior média de avaliações úteis positivas por produto.

-? g            | Lista 10 clientes que mais fizeram comentários por grupo de produto

-? q            | Encerra programa
"""

print("\n\n\n")
print(helpstring)

grupos = ["",
          "Video Games",
          "Video",
          "Toy",
          "Sports",
          "Software",
          "Music",
          "DVD",
          "CE",
          "Book",
          "Baby Product"]

while True:
    try:
        l = input('-? ')
        l = l.lower().split()
    except EOFError:
        break
    if len(l) == 0:
        continue

    if l[0] == 'q':
        break

    elif l[0] == 'a':
        try:
            sql = """
            SELECT * FROM
            (SELECT data_review, avaliacao, votos,
            utilidade, id_cliente FROM review
            WHERE asin_fk = '"""  + l[1] + """'
            ORDER BY utilidade DESC
            FETCH FIRST 10 ROW ONLY) aux
            ORDER BY avaliacao DESC, utilidade DESC;"""
        except IndexError:
            print("Comando precisa de ASIN do produto")
            continue

    elif l[0] == 'b':
        try:
            sql = """
            SELECT b.asin, b.titulo, b.ranking
            FROM produto a, produto b, similar_produto
            WHERE
            a.asin = '""" + l[1] + """' AND
            a.asin = similar_produto.asin1_fk AND
            b.asin = similar_produto.asin2 AND
            b.ranking < a.ranking AND
            b.ranking > 0;
            """
        except IndexError:
            print("Comando precisa de ASIN do produto")
            continue
    elif l[0] == 'c':
        try:
            sql = """ SELECT data_review,
            avg(avaliacao) AS avaliacao
            FROM review WHERE
            asin_fk = '""" + l[1] + """'
            GROUP BY data_review
            ORDER BY data_review;"""
        except IndexError:
            print("Comando precisa de ASIN do produto")
            continue

    elif l[0] == 'd':
        sql = "SELECT * FROM (("
        sql += " UNION ".join([f"""
            (SELECT asin, titulo, ranking, grupo
             FROM PRODUTO WHERE
             grupo = '{x}' AND ranking > 0
             ORDER BY ranking
             LIMIT 10)
        """ for x in grupos])
        sql += ")) aux ORDER BY grupo, ranking;"

    elif l[0] == 'e':
        sql = """ SELECT asin, titulo,
            avg(avaliacao) AS avaliacao FROM
            (SELECT asin_fk, avaliacao FROM review WHERE
            utilidade > votos/2 AND avaliacao > 0) aux,
            produto
            WHERE asin = asin_fk
            GROUP BY asin
            ORDER BY avaliacao DESC
            FETCH FIRST 10 ROW ONLY;"""

    elif l[0] == 'f':
        sql = """SELECT categoria_id, nome, avg_reviews_positivas FROM ( (
              SELECT categoria_id_fk AS categoria_id, AVG(cnt_review) AS avg_reviews_positivas
              FROM    ( (SELECT asin_fk, COUNT(review_id) AS cnt_review
              FROM (SELECT * FROM review WHERE avaliacao >= 4 AND utilidade > votos/2) AS rv
              GROUP BY asin_fk) AS foo
              NATURAL JOIN relacao_produto_categoria ) AS rv
              GROUP BY categoria_id_fk
              ) AS foo NATURAL JOIN categoria) AS rv
              ORDER BY avg_reviews_positivas DESC
              LIMIT 5;"""

    elif l[0] == 'g':
        sql = "SELECT * FROM (("
        sql += " UNION ".join([f"""
            (SELECT grupo, id_cliente, COUNT(*) AS tot_comment
             FROM produto JOIN review ON asin=asin_fk 
             GROUP BY id_cliente, grupo
             HAVING grupo = '{x}'
             ORDER BY tot_comment DESC
             LIMIT 10)
        """ for x in grupos])
        sql += ")) aux ORDER BY grupo, tot_comment DESC;"

    else:
        print("Consulta invalida")
        print(helpstring)
        continue


    r = subprocess.run("psql -h localhost -U postgres tp1 -c \"" + sql + "\"",
                       shell = True)
