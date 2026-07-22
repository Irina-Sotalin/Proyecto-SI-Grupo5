-- ============================================
-- Proyecto FIFA - Configuración Servidor 1
-- Base de datos: fifa_db
-- Autor: Roxana
-- ============================================

-- Creación de la base de datos
CREATE DATABASE fifa_db;
USE fifa_db;

-- Creación de la tabla 
CREATE TABLE historico_mundiales (
    version INT NOT NULL,
    team VARCHAR(100) NOT NULL,
    continent VARCHAR(50),
    is_host TINYINT,
    goals_scored_last_4y INT,
    goals_received_last_4y INT,
    wins_last_4y INT,
    losses_last_4y INT,
    draws_last_4y INT,
    world_cup_titles_before INT,
    squad_total_market_value_eur BIGINT,
    fifa_rank_pre_tournament INT,
    fifa_points_pre_tournament INT,
    squad_avg_age DECIMAL(4,1),
    world_cup_participations_before INT,
    groups_passed_before INT,
    round16_before INT,
    quarterfinals_before INT,
    semifinalists_before INT,
    finals_before INT,
    winner TINYINT,
    finalist TINYINT,
    semi_finalist TINYINT,
    quarter_finalist TINYINT
);

-- Creación del usuario para Alex (ETL remoto)
CREATE USER 'etl_alex'@'%' IDENTIFIED BY 'Proyecto2026!';
GRANT ALL PRIVILEGES ON fifa_db.* TO 'etl_alex'@'%';
FLUSH PRIVILEGES;

-- Carga de datos: train.csv
LOAD DATA INFILE '/var/lib/mysql-files/dataset_fifa_train.csv'
INTO TABLE historico_mundiales
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(version, team, continent, is_host, goals_scored_last_4y, goals_received_last_4y,
wins_last_4y, losses_last_4y, draws_last_4y, world_cup_titles_before,
@squad_total_market_value_eur, @fifa_rank_pre_tournament, @fifa_points_pre_tournament,
@squad_avg_age, @world_cup_participations_before, @groups_passed_before,
@round16_before, @quarterfinals_before, @semifinalists_before, @finals_before,
winner, finalist, semi_finalist, quarter_finalist)
SET
  squad_total_market_value_eur = NULLIF(@squad_total_market_value_eur, ''),
  fifa_rank_pre_tournament = NULLIF(@fifa_rank_pre_tournament, ''),
  fifa_points_pre_tournament = NULLIF(@fifa_points_pre_tournament, ''),
  squad_avg_age = NULLIF(@squad_avg_age, ''),
  world_cup_participations_before = NULLIF(@world_cup_participations_before, ''),
  groups_passed_before = NULLIF(@groups_passed_before, ''),
  round16_before = NULLIF(@round16_before, ''),
  quarterfinals_before = NULLIF(@quarterfinals_before, ''),
  semifinalists_before = NULLIF(@semifinalists_before, ''),
  finals_before = NULLIF(@finals_before, '');

-- Carga de datos: test.csv
LOAD DATA INFILE '/var/lib/mysql-files/dataset_fifa_test.csv'
INTO TABLE historico_mundiales
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(version, team, continent, is_host, goals_scored_last_4y, goals_received_last_4y,
wins_last_4y, losses_last_4y, draws_last_4y, world_cup_titles_before,
@squad_total_market_value_eur, @fifa_rank_pre_tournament, @fifa_points_pre_tournament,
@squad_avg_age, @world_cup_participations_before, @groups_passed_before,
@round16_before, @quarterfinals_before, @semifinalists_before, @finals_before,
@winner, @finalist, @semi_finalist, @quarter_finalist)
SET
  squad_total_market_value_eur = NULLIF(@squad_total_market_value_eur, ''),
  fifa_rank_pre_tournament = NULLIF(@fifa_rank_pre_tournament, ''),
  fifa_points_pre_tournament = NULLIF(@fifa_points_pre_tournament, ''),
  squad_avg_age = NULLIF(@squad_avg_age, ''),
  world_cup_participations_before = NULLIF(@world_cup_participations_before, ''),
  groups_passed_before = NULLIF(@groups_passed_before, ''),
  round16_before = NULLIF(@round16_before, ''),
  quarterfinals_before = NULLIF(@quarterfinals_before, ''),
  semifinalists_before = NULLIF(@semifinalists_before, ''),
  finals_before = NULLIF(@finals_before, ''),
  winner = NULLIF(@winner, ''),
  finalist = NULLIF(@finalist, ''),
  semi_finalist = NULLIF(@semi_finalist, ''),
  quarter_finalist = NULLIF(@quarter_finalist, '');

-- Verificación
SELECT COUNT(*) FROM historico_mundiales;
