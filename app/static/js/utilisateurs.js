const COULEURS_ROLE = { admin: 'bg-primary/10 text-primary', gestionnaire: 'bg-info/10 text-info' };

function pageUtilisateursData() {
    return {
        utilisateurs: [], recherche: '', filtreRole: '', tri: '', chargementEnCours: true, erreur: null, accesRefuse: false,
        modaleOuverte: false, envoiEnCours: false, erreurFormulaire: null, motDePasseVisible: false,
        formulaire: { nom: '', email: '', mot_de_passe: '', role_id: '' },

        init() {
            this.$watch('recherche', () => this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons()));
            this.$watch('filtreRole', () => this.$nextTick(() => typeof lucide !== 'undefined' && lucide.createIcons()));
        },

        utilisateurConnecteId: typeof utilisateurConnecteId !== 'undefined' ? utilisateurConnecteId : null,
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        motDePasseVisibleEdition: false,
        edition: { id: null, nom: '', email: '', mot_de_passe: '', role_id: '', actif: true },

        ouvrirModaleEdition(utilisateur) {
            this.edition = {
                id: utilisateur.id,
                nom: utilisateur.nom,
                email: utilisateur.email,
                mot_de_passe: '',
                role_id: utilisateur.role.id,
                actif: utilisateur.actif,
            };
            this.motDePasseVisibleEdition = false;
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
                const corps = {
                    nom: this.edition.nom,
                    email: this.edition.email,
                    role_id: this.edition.role_id,
                    actif: this.edition.actif,
                };
                if (this.edition.mot_de_passe) {
                    corps.mot_de_passe = this.edition.mot_de_passe;
                }

                const res = await fetch(`${urlUtilisateurs}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(corps),
                });

                let data;
                try {
                    data = await res.json();
                } catch {
                    data = { erreur: 'Erreur inattendue du serveur.' };
                }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurEdition);
                    return;
                }

                const index = this.utilisateurs.findIndex(u => u.id === this.edition.id);
                if (index !== -1) this.utilisateurs[index] = data;

                this.modaleEditionOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Utilisateur modifié avec succès.');

            } catch (err) {
                console.error('Erreur modification utilisateur :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally {
                this.editionEnCours = false;
            }
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            this.accesRefuse = false;
            try {
                const res = await fetch(urlUtilisateurs);
                if (res.status === 403) { this.accesRefuse = true; this.utilisateurs = []; return; }
                if (!res.ok) throw new Error('Réponse serveur invalide');
                this.utilisateurs = await res.json();
            } catch (err) {
                console.error('Erreur chargement utilisateurs :', err);
                this.erreur = 'Impossible de charger les utilisateurs.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        nomRole(utilisateur) { return utilisateur.role?.nom || ''; },
        utilisateursFiltres() {
            const rechercheMin = this.recherche.toLocaleLowerCase().trim();
            const filtres = this.utilisateurs.filter(utilisateur => {
                const role = this.nomRole(utilisateur);
                const nom = (utilisateur.nom || '').toLocaleLowerCase();
                const email = (utilisateur.email || '').toLocaleLowerCase();
                return (!this.filtreRole || role === this.filtreRole) && (!rechercheMin || nom.includes(rechercheMin) || email.includes(rechercheMin));
            });
            const copie = [...filtres];
            const t = this.tri;
            if (t === 'nom_desc') {
                return copie.sort((a, b) => (b.nom || '').localeCompare(a.nom || '', 'fr'));
            }
            if (t === 'role_asc') {
                return copie.sort((a, b) => (a.role?.nom || '').localeCompare(b.role?.nom || '', 'fr'));
            }
            if (t === 'date_desc') {
                return copie.sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0));
            }
            if (t === 'date_asc') {
                return copie.sort((a, b) => new Date(a.created_at || 0) - new Date(b.created_at || 0));
            }
            // Par défaut (nom_asc) : nom A → Z
            return copie.sort((a, b) => (a.nom || '').localeCompare(b.nom || '', 'fr'));
        },
        rolesDisponibles() { return [...new Set(this.utilisateurs.map(utilisateur => this.nomRole(utilisateur)).filter(Boolean))].sort((a, b) => a.localeCompare(b, 'fr')); },
        rolesPourFormulaire() {
            const roles = new Map();
            this.utilisateurs.forEach(utilisateur => { if (utilisateur.role?.id) roles.set(utilisateur.role.id, utilisateur.role); });
            return [...roles.values()].sort((a, b) => a.nom.localeCompare(b.nom, 'fr'));
        },
        couleurRole(nomRole) { return COULEURS_ROLE[nomRole] || 'bg-gray-100 text-gray-600'; },
        formaterDate(dateStr) { const date = new Date(dateStr); return Number.isNaN(date.getTime()) ? '' : date.toLocaleDateString('fr-FR'); },

        ouvrirModaleCreation() {
            this.formulaire = { nom: '', email: '', mot_de_passe: '', role_id: '' };
            this.motDePasseVisible = false;
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },
        fermerModaleCreation() { if (!this.envoiEnCours) this.modaleOuverte = false; },
        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlUtilisateurs, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
                    body: JSON.stringify({ nom: this.formulaire.nom, email: this.formulaire.email, mot_de_passe: this.formulaire.mot_de_passe, role_id: this.formulaire.role_id }),
                });
                const data = await res.json();
                if (!res.ok) {
                    this.erreurFormulaire = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurFormulaire);
                    return;
                }
                this.utilisateurs.push(data);
                this.modaleOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', 'Utilisateur créé avec succès.');
            } catch (err) {
                console.error('Erreur création utilisateur :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally { this.envoiEnCours = false; }
        },
    };
}
