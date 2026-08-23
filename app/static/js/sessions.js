const MOIS_ABREGES = ['Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin', 'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'];
const COULEURS_STATUT = {
    planifiee: { classe: 'bg-info/10 text-info', label: 'Planifiée' },
    en_cours: { classe: 'bg-warning/10 text-warning', label: 'En cours' },
    terminee: { classe: 'bg-success/10 text-success', label: 'Terminée' },
    annulee: { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

function pageSessionsData() {
    return {
        sessions: [], formations: [], formateurs: [], recherche: '', filtreStatut: '', chargementEnCours: true, erreur: null,
        modaleOuverte: false, envoiEnCours: false, erreurFormulaire: null,
        formulaire: { formation_id: '', formateur_id: '', date_debut: '', date_fin: '', type: 'intra', capacite_max: 15, lieu: '', statut: 'planifiee' },

        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        edition: {
            id: null, date_debut: '', date_fin: '', capacite_max: 0, lieu: '', statut: '',
            formation_titre: '', formateur_nom: '',
        },

        modaleSuppressionOuverte: false,
        suppressionEnCours: false,
        erreurSuppression: null,
        aSupprimer: null,

        ouvrirModaleSuppression(session) {
            this.aSupprimer = session;
            this.erreurSuppression = null;
            this.modaleSuppressionOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },

        fermerModaleSuppression() {
            if (!this.suppressionEnCours) {
                this.modaleSuppressionOuverte = false;
                this.aSupprimer = null;
            }
        },

        async confirmerSuppression() {
            this.suppressionEnCours = true;
            this.erreurSuppression = null;

            try {
                const res = await fetch(`${urlSessions}/${this.aSupprimer.id}`, {
                    method: 'DELETE',
                    credentials: 'include',
                });

                if (res.status === 204) {
                    this.sessions = this.sessions.filter(s => s.id !== this.aSupprimer.id);
                    this.modaleSuppressionOuverte = false;
                    this.aSupprimer = null;
                    return;
                }

                let data;
                try {
                    data = await res.json();
                } catch {
                    data = { erreur: 'Erreur inattendue du serveur.' };
                }
                this.erreurSuppression = data.erreur || 'Impossible de supprimer cette session.';

            } catch (err) {
                console.error('Erreur suppression session :', err);
                this.erreurSuppression = 'Impossible de contacter le serveur.';
            } finally {
                this.suppressionEnCours = false;
            }
        },

        ouvrirModaleEdition(session) {
            this.edition = {
                id: session.id,
                date_debut: session.date_debut,
                date_fin: session.date_fin,
                capacite_max: session.capacite_max,
                lieu: session.lieu || '',
                statut: session.statut,
                formation_titre: session.formation?.titre || '',
                formateur_nom: session.formateur?.nom || '',
            };
            this.erreurEdition = null;
            this.modaleEditionOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },

        fermerModaleEdition() {
            if (!this.editionEnCours) this.modaleEditionOuverte = false;
        },

        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;

            try {
                const res = await fetch(`${urlSessions}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        date_debut: this.edition.date_debut,
                        date_fin: this.edition.date_fin,
                        capacite_max: this.edition.capacite_max,
                        lieu: this.edition.lieu || null,
                        statut: this.edition.statut,
                    }),
                });

                let data;
                try {
                    data = await res.json();
                } catch {
                    data = { erreur: 'Erreur inattendue du serveur.' };
                }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    return;
                }

                const index = this.sessions.findIndex(s => s.id === this.edition.id);
                if (index !== -1) this.sessions[index] = data;

                this.modaleEditionOuverte = false;

            } catch (err) {
                console.error('Erreur modification session :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally {
                this.editionEnCours = false;
            }
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const [sessionsRes, formationsRes, formateursRes] = await Promise.all([fetch(urlSessions), fetch(urlFormations), fetch(urlFormateurs)]);
                if (!sessionsRes.ok) throw new Error('Réponse serveur invalide');
                this.sessions = await sessionsRes.json();
                if (formationsRes.ok) this.formations = await formationsRes.json();
                if (formateursRes.ok) this.formateurs = await formateursRes.json();
            } catch (err) {
                console.error('Erreur chargement sessions :', err);
                this.erreur = 'Impossible de charger les sessions.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        titreFormation(session) { return session.formation?.titre || ''; },
        nomFormateur(session) { return session.formateur?.nom || ''; },
        sessionsFiltrees() {
            const rechercheMin = this.recherche.toLocaleLowerCase().trim();
            return this.sessions.filter(session => {
                const formation = this.titreFormation(session).toLocaleLowerCase();
                const formateur = this.nomFormateur(session).toLocaleLowerCase();
                return (!this.filtreStatut || session.statut === this.filtreStatut)
                    && (!rechercheMin || formation.includes(rechercheMin) || formateur.includes(rechercheMin));
            }).sort((a, b) => new Date(b.date_debut) - new Date(a.date_debut));
        },
        formaterDate(dateStr) { const date = new Date(dateStr); return Number.isNaN(date.getTime()) ? '' : `${date.getDate()} ${MOIS_ABREGES[date.getMonth()]}`; },
        classeBadgeStatut(statut) { return COULEURS_STATUT[statut]?.classe || 'bg-gray-100 text-gray-600'; },
        labelStatut(statut) { return COULEURS_STATUT[statut]?.label || statut || ''; },
        classeBadgeRemplissage(session) {
            if (session.est_complete) return 'bg-gray-100 text-gray-600';
            if (session.taux_remplissage >= 0.7) return 'bg-success/10 text-success';
            if (session.taux_remplissage >= 0.4) return 'bg-warning/10 text-warning';
            return 'bg-danger/10 text-danger';
        },
        texteBadgeRemplissage(session) {
            if (session.est_complete) return 'Complète';
            return `${session.nb_inscrits_confirmes || 0}/${session.capacite_max || 0} (${Math.round((Number(session.taux_remplissage) || 0) * 100)}%)`;
        },

        ouvrirModaleCreation() {
            this.formulaire = { formation_id: '', formateur_id: '', date_debut: '', date_fin: '', type: 'intra', capacite_max: 15, lieu: '', statut: 'planifiee' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },
        fermerModaleCreation() { if (!this.envoiEnCours) this.modaleOuverte = false; },
        async soumettreCreation() {
            this.erreurFormulaire = null;
            if (this.formulaire.date_fin < this.formulaire.date_debut) {
                this.erreurFormulaire = 'La date de fin doit être postérieure ou égale à la date de début.';
                return;
            }
            this.envoiEnCours = true;
            try {
                const res = await fetch(urlSessions, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
                    body: JSON.stringify({
                        formation_id: this.formulaire.formation_id, formateur_id: this.formulaire.formateur_id,
                        date_debut: this.formulaire.date_debut, date_fin: this.formulaire.date_fin,
                        type: this.formulaire.type, capacite_max: this.formulaire.capacite_max,
                        lieu: this.formulaire.lieu || null, statut: this.formulaire.statut,
                    }),
                });
                const data = await res.json();
                if (!res.ok) { this.erreurFormulaire = data.erreur || 'Une erreur est survenue.'; return; }
                this.sessions.push(data);
                this.modaleOuverte = false;
            } catch (err) {
                console.error('Erreur création session :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally { this.envoiEnCours = false; }
        },
    };
}
