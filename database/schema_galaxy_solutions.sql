-- ============================================
-- Base de données : Galaxy Solutions
-- Outil de suivi et d'analyse de l'activité de formation
-- Version mise à jour : Role et Domaine en tables séparées
-- ============================================

DROP DATABASE IF EXISTS galaxy_solutions;

CREATE DATABASE galaxy_solutions
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE galaxy_solutions;

-- ============================================
-- Table : Role
-- Référentiel des 3 rôles possibles
-- ============================================
CREATE TABLE Role (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(30) NOT NULL UNIQUE
);

-- ============================================
-- Table : Domaine
-- Référentiel des 3 domaines de formation
-- Partagé entre Formation et Formateur (cohérence garantie)
-- ============================================
CREATE TABLE Domaine (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(50) NOT NULL UNIQUE
);

-- ============================================
-- Table : Utilisateur
-- Comptes des employés Galaxy Solutions (admin, gestionnaire, formateur)
-- ============================================
CREATE TABLE Utilisateur (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    mot_de_passe_hash VARCHAR(255) NOT NULL,
    role_id INT NOT NULL,
    actif BOOLEAN NOT NULL DEFAULT TRUE,
    date_creation DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id) REFERENCES Role(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- ============================================
-- Table : Formateur
-- Lien vers Utilisateur optionnel (un formateur peut exister sans compte)
-- UNIQUE sur utilisateur_id : un compte = au plus un formateur
-- ============================================
CREATE TABLE Formateur (
    id INT AUTO_INCREMENT PRIMARY KEY,
    utilisateur_id INT NULL UNIQUE,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NULL UNIQUE,
    telephone VARCHAR(20) NULL,
    domaine_id INT NOT NULL,
    FOREIGN KEY (utilisateur_id) REFERENCES Utilisateur(id)
        ON DELETE SET NULL
        ON UPDATE CASCADE,
    FOREIGN KEY (domaine_id) REFERENCES Domaine(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE
);

-- ============================================
-- Table : Formation
-- Le catalogue générique des formations proposées
-- ============================================
CREATE TABLE Formation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    titre VARCHAR(150) NOT NULL,
    domaine_id INT NOT NULL,
    duree_jours INT NOT NULL,
    description TEXT NULL,
    FOREIGN KEY (domaine_id) REFERENCES Domaine(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT chk_duree CHECK (duree_jours BETWEEN 2 AND 5)
);

-- ============================================
-- Table : Client
-- L'entreprise cliente qui inscrit ses salariés
-- ============================================
CREATE TABLE Client (
    id INT AUTO_INCREMENT PRIMARY KEY,
    nom_entreprise VARCHAR(150) NOT NULL UNIQUE,
    secteur VARCHAR(100) NULL,
    contact_email VARCHAR(150) NULL
);

-- ============================================
-- Table : Participant
-- Le salarié d'un Client qui suit réellement une formation
-- ============================================
CREATE TABLE Participant (
    id INT AUTO_INCREMENT PRIMARY KEY,
    client_id INT NOT NULL,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    FOREIGN KEY (client_id) REFERENCES Client(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE
);

-- ============================================
-- Table : Session
-- Pas de client_id direct : une session peut être inter-entreprises
-- ============================================
CREATE TABLE Session (
    id INT AUTO_INCREMENT PRIMARY KEY,
    formation_id INT NOT NULL,
    formateur_id INT NOT NULL,
    date_debut DATE NOT NULL,
    date_fin DATE NOT NULL,
    type VARCHAR(10) NOT NULL,
    capacite_max INT NOT NULL,
    lieu VARCHAR(150) NULL,
    statut VARCHAR(20) NOT NULL DEFAULT 'planifiee',
    FOREIGN KEY (formation_id) REFERENCES Formation(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    FOREIGN KEY (formateur_id) REFERENCES Formateur(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT chk_type CHECK (type IN ('intra', 'inter')),
    CONSTRAINT chk_statut_session CHECK (statut IN ('planifiee', 'en_cours', 'terminee', 'annulee')),
    CONSTRAINT chk_capacite CHECK (capacite_max > 0),
    CONSTRAINT chk_dates CHECK (date_fin >= date_debut)
);

-- ============================================
-- Table : Inscription
-- Le lien entre un Participant et une Session
-- statut = critique pour la justesse du taux de remplissage
-- ============================================
CREATE TABLE Inscription (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    participant_id INT NOT NULL,
    date_inscription DATE NOT NULL DEFAULT (CURRENT_DATE),
    statut VARCHAR(20) NOT NULL DEFAULT 'confirmee',
    FOREIGN KEY (session_id) REFERENCES Session(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    FOREIGN KEY (participant_id) REFERENCES Participant(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT chk_statut_inscription CHECK (statut IN ('confirmee', 'annulee', 'liste_attente')),
    CONSTRAINT uq_session_participant UNIQUE (session_id, participant_id)
);
