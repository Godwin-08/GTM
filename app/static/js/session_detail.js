// ============================================================
// Page /sessions/<id> : détail complet d'une session,
// avec la liste de ses inscrits et la gestion des inscriptions
// (création POST, modification statut PUT) pour admin/gestionnaire.
// ============================================================

const MOIS_ABREGES = [
    'Jan.', 'Fév.', 'Mars', 'Avril', 'Mai', 'Juin',
    'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.'
];

const COULEURS_STATUT_SESSION = {
    'planifiee': { classe: 'bg-info/10 text-info', label: 'Planifiée' },
    'en_cours': { classe: 'bg-warning/10 text-warning', label: 'En cours' },
    'terminee': { classe: 'bg-success/10 text-success', label: 'Terminée' },
    'annulee': { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

const COULEURS_STATUT_INSCRIPTION = {
    'confirmee': { classe: 'bg-success/10 text-success', label: 'Confirmée' },
    'liste_attente': { classe: 'bg-warning/10 text-warning', label: "Liste d'attente" },
    'annulee': { classe: 'bg-gray-100 text-gray-600', label: 'Annulée' },
};

// sessionId et peutGererInscriptions passés depuis Jinja :
// x-data="pageSessionDetailData({{ session_id }}, {{ 'true' if ... else 'false' }})"
function pageSessionDetailData(sessionId, peutGererInscriptions) {
    return {
        session: null,
        inscriptions: [],
        chargementEnCours: true,
        erreur: null,

        // ── Gestion des inscriptions ──────────────────────────────
        peutGererInscriptions: !!peutGererInscriptions,
        clients: [],
        participants: [],
        chargementParticipants: false,

        // Modale ajout
        modaleAjoutOuverte: false,
        ajoutEnCours: false,
        formulaire: {
            client_id: '',
            participant_id: '',
            statut: 'confirmee',
        },

        // Suivi local des statuts candidats pour validation explicite par ligne
        statutsCandidats: {},
        enCoursDeChargementStatut: {},

        // ── Chargement initial ────────────────────────────────────
        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;

            try {
                const appels = [
                    fetch(`/api/sessions/${sessionId}`),
                    fetch(`/api/inscriptions?session_id=${sessionId}`),
                ];
                // Charger uniquement les clients si l'utilisateur a le droit de gérer
                if (this.peutGererInscriptions) {
                    appels.push(fetch('/api/clients'));
                }

                const resultats = await Promise.all(appels);
                const [resSession, resInscriptions] = resultats;

                if (!resSession.ok) throw new Error('Session introuvable');
                this.session = await resSession.json();

                if (resInscriptions.ok) {
                    const listeInscriptions = await resInscriptions.json();
                    this.inscriptions = listeInscriptions;
                    this.initialiserStatutsCandidats(listeInscriptions);
                }

                if (this.peutGererInscriptions && resultats.length === 3) {
                    const [, , resClients] = resultats;
                    if (resClients.ok) this.clients = await resClients.json();
                }

            } catch (err) {
                console.error('Erreur chargement détail session :', err);
                this.erreur = 'Impossible de charger cette session.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => {
                    if (window.lucide && typeof window.lucide.createIcons === 'function') {
                        window.lucide.createIcons();
                    }
                });
            }
        },

        // Synchronise la carte des statuts candidats avec les statuts réels serveur
        initialiserStatutsCandidats(listeInscriptions) {
            const statuts = {};
            const chargements = {};
            (listeInscriptions || []).forEach(ins => {
                statuts[ins.id] = ins.statut;
                chargements[ins.id] = false;
            });
            this.statutsCandidats = statuts;
            this.enCoursDeChargementStatut = chargements;
        },

        // ── Rechargement partiel après mutation ──────────────────
        async rechargerInscriptionsEtSession() {
            try {
                const [resInscriptions, resSession] = await Promise.all([
                    fetch(`/api/inscriptions?session_id=${sessionId}`),
                    fetch(`/api/sessions/${sessionId}`),
                ]);
                if (resInscriptions.ok) {
                    const meInscriptions = await resInscriptions.json();
                    this.inscriptions = meInscriptions;
                    this.initialiserStatutsCandidats(meInscriptions);
                }
                if (resSession.ok) this.session = await resSession.json();
            } catch (err) {
                console.error('Erreur rechargement :', err);
            } finally {
                this.$nextTick(() => {
                    if (window.lucide && typeof window.lucide.createIcons === 'function') {
                        window.lucide.createIcons();
                    }
                });
            }
        },

        // ── Modale ajout : Ouverture & Fermeture sécurisées ───────
        statutInitialModale() {
            return (this.session && this.session.est_complete) ? 'liste_attente' : 'confirmee';
        },

        ouvrirModaleAjout() {
            this.formulaire = {
                client_id: '',
                participant_id: '',
                statut: this.statutInitialModale(),
            };
            this.participants = [];
            this.chargementParticipants = false;
            this.modaleAjoutOuverte = true;
        },

        fermerModaleAjout() {
            this.modaleAjoutOuverte = false;
            this.formulaire = {
                client_id: '',
                participant_id: '',
                statut: this.statutInitialModale(),
            };
            this.participants = [];
            this.chargementParticipants = false;
        },

        // ── Chargement dynamique des participants par client ─────
        async changerClient() {
            this.formulaire.participant_id = '';
            this.participants = [];

            if (!this.formulaire.client_id) return;

            this.chargementParticipants = true;
            try {
                const res = await fetch(`/api/participants?client_id=${this.formulaire.client_id}`);
                if (res.ok) {
                    this.participants = await res.json();
                } else {
                    const data = await res.json();
                    if (typeof window.afficherToast === 'function') {
                        window.afficherToast('erreur', data.erreur || 'Erreur lors de la récupération des participants.');
                    }
                }
            } catch (err) {
                console.error('Erreur chargement participants client :', err);
                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('erreur', 'Impossible de contacter le serveur.');
                }
            } finally {
                this.chargementParticipants = false;
            }
        },

        // ── Création d'une inscription ───────────────────────────
        async ajouterInscription() {
            if (!this.formulaire.participant_id) return;
            this.ajoutEnCours = true;
            try {
                const res = await fetch('/api/inscriptions', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessionId,
                        participant_id: Number(this.formulaire.participant_id),
                        statut: this.formulaire.statut,
                    }),
                });
                const data = await res.json();
                if (!res.ok) {
                    if (typeof window.afficherToast === 'function') {
                        window.afficherToast('erreur', data.erreur || 'Une erreur est survenue.');
                    }
                    return;
                }
                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('succes', 'Inscription ajoutée avec succès.');
                }
                this.fermerModaleAjout();
                await this.rechargerInscriptionsEtSession();
            } catch (err) {
                console.error('Erreur ajout inscription :', err);
                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('erreur', 'Impossible de contacter le serveur.');
                }
            } finally {
                this.ajoutEnCours = false;
            }
        },

        // ── Modification explicite du statut avec anti-double-clic & rollback ──
        async confirmerChangementStatut(inscription) {
            const id = inscription.id;
            const nouveauStatut = this.statutsCandidats[id];

            if (!nouveauStatut || nouveauStatut === inscription.statut) return;

            this.enCoursDeChargementStatut[id] = true;
            try {
                const res = await fetch(`/api/inscriptions/${id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ statut: nouveauStatut }),
                });
                const data = await res.json();
                if (!res.ok) {
                    // Restauration explicite de l'ancien statut serveur
                    this.statutsCandidats[id] = inscription.statut;
                    if (typeof window.afficherToast === 'function') {
                        window.afficherToast('erreur', data.erreur || 'Modification impossible.');
                    }
                    return;
                }

                // Succès : mise à jour du statut serveur et confirmation
                inscription.statut = nouveauStatut;
                this.statutsCandidats[id] = nouveauStatut;

                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('succes', 'Statut mis à jour.');
                }

                // Resynchroniser les KPI session
                const resSession = await fetch(`/api/sessions/${sessionId}`);
                if (resSession.ok) this.session = await resSession.json();

            } catch (err) {
                // Restauration explicite de l'ancien statut serveur
                this.statutsCandidats[id] = inscription.statut;
                console.error('Erreur modification statut :', err);
                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('erreur', 'Impossible de contacter le serveur.');
                }
            } finally {
                this.enCoursDeChargementStatut[id] = false;
            }
        },

        // ── Helpers d'affichage ──────────────────────────────────
        formaterDate(dateStr) {
            if (!dateStr) return '—';
            const d = new Date(dateStr);
            return `${d.getDate()} ${MOIS_ABREGES[d.getMonth()]} ${d.getFullYear()}`;
        },

        labelStatut(statut) {
            return (COULEURS_STATUT_SESSION[statut] || { label: statut }).label;
        },
        classeBadgeStatut(statut) {
            return (COULEURS_STATUT_SESSION[statut] || { classe: 'bg-gray-100 text-gray-600' }).classe;
        },

        labelInscription(statut) {
            return (COULEURS_STATUT_INSCRIPTION[statut] || { label: statut }).label;
        },
        classeBadgeInscription(statut) {
            return (COULEURS_STATUT_INSCRIPTION[statut] || { classe: 'bg-gray-100 text-gray-600' }).classe;
        },
    };
}
