const COULEURS_DOMAINE = {
    'Web & Data': 'bg-info/10 text-info',
    'Management Agile': 'bg-success/10 text-success',
    'Cybersécurité': 'bg-danger/10 text-danger',
};

function pageFormateursData() {
    return {
        formateurs: [], domaines: [], recherche: '', filtreDomaine: '', filtreType: '', chargementEnCours: true, erreur: null,
        modaleOuverte: false, envoiEnCours: false, erreurFormulaire: null,
        formulaire: { nom: '', domaine_id: '', email: '', telephone: '', utilisateur_id: '' },
        modaleEditionOuverte: false, editionEnCours: false, erreurEdition: null,
        edition: { id: null, nom: '', domaine_id: '', email: '', telephone: '', a_un_compte: false },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const [formateursRes, domainesRes] = await Promise.all([fetch(urlFormateurs), fetch(urlDomaines)]);
                if (!formateursRes.ok) throw new Error('Réponse serveur invalide');
                this.formateurs = await formateursRes.json();
                if (domainesRes.ok) this.domaines = await domainesRes.json();
            } catch (err) {
                console.error('Erreur chargement formateurs :', err);
                this.erreur = 'Impossible de charger les formateurs.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        nomDomaine(formateur) { return formateur.domaine?.nom || ''; },
        formateursFiltres() {
            const rechercheMin = this.recherche.toLocaleLowerCase().trim();
            return this.formateurs.filter(formateur => {
                const domaine = this.nomDomaine(formateur);
                const nom = (formateur.nom || '').toLocaleLowerCase();
                return (!this.filtreDomaine || domaine === this.filtreDomaine)
                    && (this.filtreType !== 'interne' || formateur.a_un_compte)
                    && (this.filtreType !== 'externe' || !formateur.a_un_compte)
                    && (!rechercheMin || nom.includes(rechercheMin));
            });
        },
        domainesDisponibles() { return this.domaines.map(domaine => domaine.nom).sort((a, b) => a.localeCompare(b, 'fr')); },
        couleurDomaine(nomDomaine) { return COULEURS_DOMAINE[nomDomaine] || 'bg-gray-100 text-gray-600'; },

        ouvrirModaleCreation() {
            this.formulaire = { nom: '', domaine_id: '', email: '', telephone: '', utilisateur_id: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },
        fermerModaleCreation() { if (!this.envoiEnCours) this.modaleOuverte = false; },
        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlFormateurs, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
                    body: JSON.stringify({
                        nom: this.formulaire.nom,
                        domaine_id: this.formulaire.domaine_id,
                        email: this.formulaire.email || null,
                        telephone: this.formulaire.telephone || null,
                        ...(this.formulaire.utilisateur_id ? { utilisateur_id: this.formulaire.utilisateur_id } : {}),
                    }),
                });
                const data = await res.json();
                if (!res.ok) { this.erreurFormulaire = data.erreur || 'Une erreur est survenue.'; return; }
                this.formateurs.push(data);
                this.modaleOuverte = false;
            } catch (err) {
                console.error('Erreur création formateur :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally { this.envoiEnCours = false; }
        },

        ouvrirModaleEdition(formateur) {
            this.edition = {
                id: formateur.id,
                nom: formateur.nom,
                domaine_id: formateur.domaine?.id ?? '',
                email: formateur.email || '',
                telephone: formateur.telephone || '',
                a_un_compte: formateur.a_un_compte,
            };
            this.erreurEdition = null;
            this.modaleEditionOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },
        fermerModaleEdition() { if (!this.editionEnCours) this.modaleEditionOuverte = false; },
        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;
            try {
                const res = await fetch(`${urlFormateurs}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        nom: this.edition.nom,
                        domaine_id: this.edition.domaine_id,
                        email: this.edition.email || null,
                        telephone: this.edition.telephone || null,
                    }),
                });

                let data;
                try { data = await res.json(); } catch { data = { erreur: 'Erreur inattendue du serveur.' }; }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    return;
                }

                const index = this.formateurs.findIndex(f => f.id === this.edition.id);
                if (index !== -1) this.formateurs[index] = data;
                this.modaleEditionOuverte = false;
            } catch (err) {
                console.error('Erreur modification formateur :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally { this.editionEnCours = false; }
        },
    };
}
