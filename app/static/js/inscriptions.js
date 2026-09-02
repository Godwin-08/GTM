const COULEURS_STATUT_INSCRIPTION = {
    confirmee: 'bg-success/10 text-success',
    annulee: 'bg-gray-100 text-gray-600',
    liste_attente: 'bg-warning/10 text-warning',
};

function pageInscriptionsData() {
    return {
        inscriptions: [],
        sessions: [],
        formations: [],
        clients: [],
        participants: [],
        chargementEnCours: true,
        erreur: null,
        filtres: {
            statut: '',
            session_id: '',
            formation_id: '',
            client_id: '',
            participant_id: '',
            date_debut_min: '',
            date_debut_max: '',
        },

        init() {
            window.addEventListener('popstate', () => {
                this.lireFiltresDepuisUrl();
                this.appliquerFiltres(true, false);
            });
        },

        lireFiltresDepuisUrl() {
            const params = new URLSearchParams(window.location.search);
            this.filtres.statut = params.get('statut') || '';
            this.filtres.formation_id = params.get('formation_id') || '';
            this.filtres.session_id = params.get('session_id') || '';
            this.filtres.client_id = params.get('client_id') || '';
            this.filtres.participant_id = params.get('participant_id') || '';
            this.filtres.date_debut_min = params.get('date_debut_min') || '';
            this.filtres.date_debut_max = params.get('date_debut_max') || '';
        },

        synchroniserUrlNavigateur(reinitialiser = false) {
            if (reinitialiser) {
                if (window.location.search) {
                    window.history.pushState(null, '', window.location.pathname);
                }
                return;
            }
            const params = new URLSearchParams();
            Object.entries(this.filtres).forEach(([cle, valeur]) => {
                if (valeur !== '' && valeur !== null && valeur !== undefined) {
                    params.set(cle, valeur);
                }
            });
            const query = params.toString();
            const cible = query ? `${window.location.pathname}?${query}` : window.location.pathname;
            if (window.location.pathname + window.location.search !== cible) {
                window.history.pushState(null, '', cible);
            }
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const resultats = await Promise.all([
                    fetch(urlSessions),
                    fetch(urlFormations),
                    fetch(urlClients),
                    fetch(urlParticipants),
                ]);
                const [sessionsRes, formationsRes, clientsRes, participantsRes] = resultats;
                if (![sessionsRes, formationsRes, clientsRes, participantsRes].every(res => res.ok)) {
                    throw new Error('Réponse serveur invalide');
                }
                [this.sessions, this.formations, this.clients, this.participants] = await Promise.all(
                    resultats.map(res => res.json())
                );
                this.lireFiltresDepuisUrl();
                await this.appliquerFiltres(false, false);
            } catch (err) {
                console.error('Erreur chargement inscriptions :', err);
                this.erreur = 'Impossible de charger les inscriptions.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        urlFiltree() {
            const params = new URLSearchParams();
            Object.entries(this.filtres).forEach(([cle, valeur]) => {
                if (valeur !== '' && valeur !== null && valeur !== undefined) {
                    params.set(cle, valeur);
                }
            });
            return params.toString() ? `${urlInscriptions}?${params}` : urlInscriptions;
        },

        async appliquerFiltres(gererChargement = true, majHistorique = true) {
            if (this.filtres.date_debut_min && this.filtres.date_debut_max && this.filtres.date_debut_min > this.filtres.date_debut_max) {
                this.erreur = 'La date minimale doit être antérieure ou égale à la date maximale.';
                return;
            }
            if (gererChargement) this.chargementEnCours = true;
            this.erreur = null;
            if (majHistorique) {
                this.synchroniserUrlNavigateur(false);
            }
            try {
                const res = await fetch(this.urlFiltree());
                const data = await res.json();
                if (!res.ok) throw new Error(data.erreur || 'Réponse serveur invalide');
                this.inscriptions = data;
            } catch (err) {
                console.error('Erreur filtrage inscriptions :', err);
                this.inscriptions = [];
                this.erreur = err.message || 'Impossible de charger les inscriptions.';
            } finally {
                if (gererChargement) this.chargementEnCours = false;
                this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons());
            }
        },

        reinitialiserFiltres() {
            this.filtres = {
                statut: '',
                session_id: '',
                formation_id: '',
                client_id: '',
                participant_id: '',
                date_debut_min: '',
                date_debut_max: '',
            };
            this.synchroniserUrlNavigateur(true);
            this.appliquerFiltres(true, false);
        },

        sessionsFiltreesParFormation() {
            if (!this.filtres.formation_id) return this.sessions;
            return this.sessions.filter(s => String(s.formation?.id) === String(this.filtres.formation_id));
        },

        participantsFiltresParClient() {
            if (!this.filtres.client_id) return this.participants;
            return this.participants.filter(p => String(p.client?.id) === String(this.filtres.client_id));
        },

        changerFormation() {
            const sessionsDispo = this.sessionsFiltreesParFormation();
            if (!sessionsDispo.some(s => String(s.id) === String(this.filtres.session_id))) {
                this.filtres.session_id = '';
            }
        },

        changerClient() {
            const participantsDispo = this.participantsFiltresParClient();
            if (!participantsDispo.some(p => String(p.id) === String(this.filtres.participant_id))) {
                this.filtres.participant_id = '';
            }
        },

        aDesFiltresActifs() {
            return Object.values(this.filtres).some(v => v !== '' && v !== null && v !== undefined);
        },

        libelleSession(session) {
            return `${session.formation?.titre || 'Formation'} — ${session.date_debut}`;
        },

        libelleStatut(statut) {
            const labels = {
                confirmee: 'Confirmée',
                annulee: 'Annulée',
                liste_attente: "Liste d'attente",
            };
            return labels[statut] || statut;
        },

        classeStatut(statut) {
            return COULEURS_STATUT_INSCRIPTION[statut] || 'bg-gray-100 text-gray-600';
        },
    };
}
