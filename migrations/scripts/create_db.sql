select 'create database auth' where not exists (select from pg_database where datname = 'auth')\gexec
\c auth
