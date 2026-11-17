// ============================================================
// Page /domaines : gestion du référentiel des domaines d'expertise.
// CRUD complet : liste, création, modification, suppression sécurisée.
// ============================================================

function pageDomainesData() {
    return {
        domaines: [],
        modeSelection: false,
        selectionnees: [],
        recherche: '',
        tri: 'nom_asc',
        chargementEnCours: true,
        erreur: null,

        // Modale de création
        modaleCreationOuverte: false,
        envoiEnCours: false,
        erreurCreation: null,
        formulaireCreation: { nom: '' },

        // Modale d'édition
        modaleEditionOuverte: false,
        editionEnCours: false,
        erreurEdition: null,
        formulaireEdition: { id: null, nom: '' },
        modaleSuppressionOuverte: false,
        erreurSuppression: null,
        aSupprimer: null,

        // Modales de consultation des formations et formateurs
        domaineSelectionne: null,
        chargementDetailsDomaine: false,
        modaleFormationsOuverte: false,
        modaleFormateursOuverte: false,

        async chargerDetailsDomaine(domaineId) {
            this.chargementDetailsDomaine = true;
            try {
                const res = await fetch(`${urlDomaines}/${domaineId}`);
                if (res.ok) {
                    const data = await res.json();
                    this.domaineSelectionne = data;
                }
            } catch (err) {
                console.error('Erreur chargement détails domaine :', err);
            } finally {
                this.chargementDetailsDomaine = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        ouvrirModaleFormations(domaine) {
            this.domaineSelectionne = { ...domaine, formations: [] };
            this.modaleFormationsOuverte = true;
            this.chargerDetailsDomaine(domaine.id);
            this.$nextTick(() => lucide.createIcons());
        },

        ouvrirModaleFormateurs(domaine) {
            this.domaineSelectionne = { ...domaine, formateurs: [] };
            this.modaleFormateursOuverte = true;
            this.chargerDetailsDomaine(domaine.id);
            this.$nextTick(() => lucide.createIcons());
        },

        // --------------------------------------------------------
        // Chargement initial
        // --------------------------------------------------------
        async charger() {
            this.chargementEnCours = true;
            this.erreur = null;
            try {
                const res = await fetch(urlDomaines);
                if (!res.ok) throw new Error('Réponse serveur invalide');
                this.domaines = await res.json();
            } catch (err) {
                console.error('Erreur chargement domaines :', err);
                this.erreur = 'Impossible de charger les domaines.';
            } finally {
                this.chargementEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        // --------------------------------------------------------
        // Filtrage local
        // --------------------------------------------------------
        domainesFiltres() {
            const q = this.recherche.toLowerCase().trim();
            const filtres = q
                ? this.domaines.filter(d => (d.nom || '').toLowerCase().includes(q))
                : [...this.domaines];
            return filtres.sort((a, b) => {
                if (this.tri === 'formations_desc') return (b.nb_formations || 0) - (a.nb_formations || 0);
                if (this.tri === 'formateurs_desc') return (b.nb_formateurs || 0) - (a.nb_formateurs || 0);
                return (a.nom || '').localeCompare(b.nom || '', 'fr');
            });
        },

        // --------------------------------------------------------
        // Création
        // --------------------------------------------------------
        basculerModeSelection() {
            this.modeSelection = !this.modeSelection;
            this.selectionnees = [];
        },
        toggleSelection(id) {
            this.selectionnees = this.selectionnees.includes(id) ? this.selectionnees.filter(item => item !== id) : [...this.selectionnees, id];
        },
        toggleSelectionGlobale() {
            const visibles = this.domainesFiltres().map(domaine => domaine.id);
            const tousSelectionnes = visibles.length > 0 && visibles.every(id => this.selectionnees.includes(id));
            this.selectionnees = tousSelectionnes ? this.selectionnees.filter(id => !visibles.includes(id)) : [...new Set([...this.selectionnees, ...visibles])];
        },
        async supprimerSelection() {
            if (!this.selectionnees.length || !await window.demanderConfirmation(`${this.selectionnees.length} domaine(s) sélectionné(s) seront définitivement supprimé(s).`)) return;
            try {
                const res = await fetch(urlDomaines, { method: 'DELETE', headers: { 'Content-Type': 'application/json' }, credentials: 'include', body: JSON.stringify({ ids: this.selectionnees }) });
                const data = await res.json().catch(() => ({}));
                if (!res.ok) throw new Error(data.erreur || 'Suppression impossible.');
                this.domaines = this.domaines.filter(domaine => !this.selectionnees.includes(domaine.id));
                this.modeSelection = false; this.selectionnees = [];
                window.afficherToast?.('succes', `${data.supprimees.length} domaine(s) supprimé(s).`);
            } catch (err) { window.afficherToast?.('erreur', err.message); }
        },

        ouvrirModaleCreation() {
            this.formulaireCreation = { nom: '' };
            this.erreurCreation = null;
            this.modaleCreationOuverte = true;
            this.$nextTick(() => {
                lucide.createIcons();
                const input = document.getElementById('domaine-nom');
                if (input) input.focus();
            });
        },

        async soumettreCreation() {
            this.envoiEnCours = true;
            this.erreurCreation = null;
            try {
                const res = await fetch(urlDomaines, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ nom: this.formulaireCreation.nom }),
                });
                const data = await res.json();
                if (!res.ok) {
                    this.erreurCreation = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurCreation);
                    return;
                }
                this.domaines.push(data);
                this.modaleCreationOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', `Domaine "${data.nom}" créé avec succès.`);
            } catch (err) {
                console.error('Erreur création domaine :', err);
                this.erreurCreation = 'Impossible de contacter le serveur.';
            } finally {
                this.envoiEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        // --------------------------------------------------------
        // Édition
        // --------------------------------------------------------
        ouvrirModaleEdition(domaine) {
            this.formulaireEdition = { id: domaine.id, nom: domaine.nom };
            this.erreurEdition = null;
            this.modaleEditionOuverte = true;
            this.$nextTick(() => {
                lucide.createIcons();
                const input = document.getElementById('domaine-edition-nom');
                if (input) input.focus();
            });
        },

        async soumettreEdition() {
            this.editionEnCours = true;
            this.erreurEdition = null;
            try {
                const res = await fetch(`${urlDomaines}/${this.formulaireEdition.id}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify({ nom: this.formulaireEdition.nom }),
                });
                const data = await res.json();
                if (!res.ok) {
                    this.erreurEdition = data.erreur || 'Une erreur est survenue.';
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', this.erreurEdition);
                    return;
                }
                const index = this.domaines.findIndex(d => d.id === this.formulaireEdition.id);
                if (index !== -1) this.domaines[index] = data;
                this.modaleEditionOuverte = false;
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', `Domaine "${data.nom}" modifié avec succès.`);
            } catch (err) {
                console.error('Erreur modification domaine :', err);
                this.erreurEdition = 'Impossible de contacter le serveur.';
            } finally {
                this.editionEnCours = false;
                this.$nextTick(() => lucide.createIcons());
            }
        },

        // --------------------------------------------------------
        // Suppression avec confirmation visuelle commune
        // --------------------------------------------------------
        ouvrirModaleSuppression(domaine) {
            this.aSupprimer = domaine;
            this.erreurSuppression = null;
            this.modaleSuppressionOuverte = true;
        },
        fermerModaleSuppression() {
            this.modaleSuppressionOuverte = false;
            this.aSupprimer = null;
            this.erreurSuppression = null;
        },
        async confirmerSuppression(domaine = this.aSupprimer) {
            const nbLies = (domaine.nb_formations || 0) + (domaine.nb_formateurs || 0);
            if (nbLies > 0) {
                this.erreurSuppression = `Impossible de supprimer "${domaine.nom}" : ${domaine.nb_formations} formation(s) et ${domaine.nb_formateurs} formateur(s) sont liés à ce domaine.`;
                return;
            }
            if (nbLies > 0) {
                if (typeof window.afficherToast === 'function') {
                    window.afficherToast('erreur', `Impossible de supprimer "${domaine.nom}" : ${domaine.nb_formations} formation(s) et ${domaine.nb_formateurs} formateur(s) sont liés à ce domaine.`);
                } else {
                    alert(`Impossible de supprimer "${domaine.nom}" : des formations ou formateurs y sont encore rattachés.`);
                }
                return;
            }

            const confirme = await window.demanderConfirmation(
                `Le domaine « ${domaine.nom} » sera définitivement supprimé. Cette action est irréversible.`
            );
            if (!confirme) return;

            try {
                const res = await fetch(`${urlDomaines}/${domaine.id}`, {
                    method: 'DELETE',
                    credentials: 'include',
                });
                const data = await res.json();
                if (!res.ok) {
                    if (typeof window.afficherToast === 'function') window.afficherToast('erreur', data.erreur || 'Suppression impossible.');
                    return;
                }
                this.domaines = this.domaines.filter(d => d.id !== domaine.id);
                if (typeof window.afficherToast === 'function') window.afficherToast('succes', data.message || `Domaine supprimé avec succès.`);
            } catch (err) {
                console.error('Erreur suppression domaine :', err);
                if (typeof window.afficherToast === 'function') window.afficherToast('erreur', 'Erreur réseau lors de la suppression.');
            } finally {
                this.$nextTick(() => lucide.createIcons());
            }
        },
    };
}
