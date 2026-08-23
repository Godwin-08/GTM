const COULEURS_DOMAINE = {
    'Web & Data': 'bg-info/10 text-info',
    'Management Agile': 'bg-success/10 text-success',
    'Cybersécurité': 'bg-danger/10 text-danger',
};

function pageFormationsData() {
    return {
        formations: [], domaines: [], recherche: '', filtreDomaine: '', chargementEnCours: true, erreur: null,
        modaleOuverte: false, envoiEnCours: false, erreurFormulaire: null,
        formulaire: { titre: '', domaine_id: '', duree_jours: 3, description: '' },
        modaleEditionOuverte: false, editionEnCours: false, erreurEdition: null,
        edition: { id: null, titre: '', domaine_id: '', duree_jours: 3, description: '' },

        modaleSuppressionOuverte: false,
        suppressionEnCours: false,
        erreurSuppression: null,
        aSupprimer: null,

        ouvrirModaleSuppression(formation) {
            this.aSupprimer = formation;
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
                const res = await fetch(`${urlFormations}/${this.aSupprimer.id}`, {
                    method: 'DELETE',
                    credentials: 'include',
                });

                if (res.status === 204) {
                    this.formations = this.formations.filter(f => f.id !== this.aSupprimer.id);
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
                this.erreurSuppression = data.erreur || 'Impossible de supprimer cette formation.';

            } catch (err) {
                console.error('Erreur suppression formation :', err);
                this.erreurSuppression = 'Impossible de contacter le serveur.';
            } finally {
                this.suppressionEnCours = false;
            }
        },

        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const [formationsRes, domainesRes] = await Promise.all([fetch(urlFormations), fetch(urlDomaines)]);
                if (!formationsRes.ok || !domainesRes.ok) throw new Error('Réponse serveur invalide');
                this.formations = await formationsRes.json();
                this.domaines = await domainesRes.json();
            } catch (err) {
                console.error('Erreur chargement formations :', err);
                this.erreur = 'Impossible de charger les formations.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        nomDomaine(formation) { return formation.domaine?.nom || ''; },
        formationsFiltrees() {
            const rechercheMin = this.recherche.toLocaleLowerCase().trim();
            return this.formations.filter(formation => {
                const titre = (formation.titre || '').toLocaleLowerCase();
                const domaine = this.nomDomaine(formation);
                return (!this.filtreDomaine || domaine === this.filtreDomaine) && (!rechercheMin || titre.includes(rechercheMin));
            });
        },
        domainesDisponibles() { return this.domaines.map(domaine => domaine.nom).sort((a, b) => a.localeCompare(b, 'fr')); },
        couleurDomaine(nomDomaine) { return COULEURS_DOMAINE[nomDomaine] || 'bg-gray-100 text-gray-600'; },

        ouvrirModaleCreation() {
            this.formulaire = { titre: '', domaine_id: '', duree_jours: 3, description: '' };
            this.erreurFormulaire = null;
            this.modaleOuverte = true;
            this.$nextTick(() => lucide.createIcons());
        },
        fermerModaleCreation() { if (!this.envoiEnCours) this.modaleOuverte = false; },
        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurFormulaire = null;
            try {
                const res = await fetch(urlFormations, {
                    method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'include',
                    body: JSON.stringify({ titre: this.formulaire.titre, domaine_id: this.formulaire.domaine_id, duree_jours: this.formulaire.duree_jours, description: this.formulaire.description || null }),
                });
                const data = await res.json();
                if (!res.ok) { this.erreurFormulaire = data.erreur || 'Une erreur est survenue.'; return; }
                this.formations.push(data);
                this.modaleOuverte = false;
            } catch (err) {
                console.error('Erreur création formation :', err);
                this.erreurFormulaire = 'Impossible de contacter le serveur.';
            } finally { this.envoiEnCours = false; }
        },

        ouvrirModaleEdition(formation) {
            this.edition = {
                id: formation.id,
                titre: formation.titre,
                domaine_id: formation.domaine?.id ?? '',
                duree_jours: formation.duree_jours,
                description: formation.description || '',
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
                const res = await fetch(`${urlFormations}/${this.edition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({
                        titre: this.edition.titre,
                        domaine_id: this.edition.domaine_id,
                        duree_jours: this.edition.duree_jours,
                        description: this.edition.description || null,
                    }),
                });

                let data;
                try { data = await res.json(); } catch { data = { erreur: 'Erreur inattendue du serveur.' }; }

                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    return;
                }

                const index = this.formations.findIndex(f => f.id === this.edition.id);
                if (index !== -1) this.formations[index] = data;
                this.modaleEditionOuverte = false;
            } catch (err) {
                console.error('Erreur modification formation :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally { this.editionEnCours = false; }
        },
    };
}
