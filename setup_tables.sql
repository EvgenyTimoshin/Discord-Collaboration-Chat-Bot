-- noinspection SqlDialectInspectionForFile
-- noinspection SqlNoDataSourceInspectionForFile

CREATE TABLE IF NOT EXISTS Reminders(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  reminderText VARCHAR(1000) NOT NULL,
  timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  endTime TIMESTAMP,
  authorName VARCHAR(50) NOT NULL,
  discordId VARCHAR(50) NOT NULL,
  targetedGroup VARCHAR(50) DEFAULT 'everyone',
  finished INT(1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Roles (
  discordID VARCHAR(50) PRIMARY KEY,
  discordName VARCHAR(50) UNIQUE,
  role VARCHAR(50) DEFAULT 'Developer'
);

CREATE TABLE IF NOT EXISTS Projects (

  name VARCHAR(50) PRIMARY KEY DEFAULT 'Collab  Project',
  repo VARCHAR (100) NOT NULL,
  finished INT(1) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS Gists (
  link VARCHAR (100) PRIMARY KEY NOT NULL,
  gistName VARCHAR (100)
);