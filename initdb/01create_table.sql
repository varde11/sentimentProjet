CREATE TABLE client (
    id_client SERIAL PRIMARY KEY,
    nom VARCHAR (20) NOT NULL,
    langue CHAR(2)
);

CREATE TABLE produit (
    id_produit SERIAL PRIMARY KEY,
    lien VARCHAR(60) NOT NULL,
    detail TEXT NOT NULL 
);

