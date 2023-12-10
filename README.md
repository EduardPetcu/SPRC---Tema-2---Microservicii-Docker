Petcu Eduard - 344C1

# Rulare tema + pgadmin
Tema se ruleaza executand comanda `docker-compose up --build` in directorul
principal.
Pentru a vedea tabelele construite prin intermediul utilitarului folosit
`pgAdmin` [1] se poate intra pe browser la localhost:5050 si login cu 
credentialele:
- email: admin@admin.com
- password: admin
Mai departe, se adauga un nou server:
- General -> Name: se alege un nume la liber pentru server
- Connection -> Host name/address: weather_db
- Username -> postgres
- Password -> postgres
Dupa aceea, se pot realiza operatii pe tabele din acest utilitar. 

# Alegerea microserviciilor
Am ales sa lucrez in python flask si SQLAlchemy iar un mare impact in alegerea
acestora l-a avut un tutorial [2] care explica lucrurile de baza despre 
interactiunea python flask-ului cu bazele de date 

# Referinte
[1] : https://github.com/pgadmin-org/pgadmin4

[2] : https://www.youtube.com/watch?v=fHQWTsWqBdE&t