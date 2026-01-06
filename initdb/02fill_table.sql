COPY client (nom,langue)
FROM '/docker-entrypoint-initdb.d/clients.csv'
DELIMITER ','
CSV HEADER;

COPY produit (lien,detail)
FROM '/docker-entrypoint-initdb.d/produits.csv'
DELIMITER ','
CSV HEADER;