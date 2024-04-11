# -*- coding: utf-8 -*-

# eopayment - online payment library
# Copyright (C) 2011-2020 Entr'ouvert
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


'''Responses codes emitted by EMV Card or 'Carte Bleu' in France'''

CB_RESPONSE_CODES = {
    '00': 'Transaction approuvée ou traitée avec succès',
    '02': 'Contacter l\'émetteur de carte',
    '03': 'Accepteur invalide',
    '04': 'Conserver la carte',
    '05': 'Ne pas honorer',
    '07': 'Conserver la carte, conditions spéciales',
    '08': 'Approuver après identification',
    '12': 'Transaction invalide',
    '13': 'Montant invalide',
    '14': 'Numéro de porteur invalide',
    '15': 'Emetteur de carte inconnu',
    '30': 'Erreur de format',
    '31': 'Identifiant de l\'organisme acquéreur inconnu',
    '33': 'Date de validité de la carte dépassée',
    '34': 'Suspicion de fraude',
    '41': 'Carte perdue',
    '43': 'Carte volée',
    '51': 'Provision insuffisante ou crédit dépassé',
    '54': 'Date de validité de la carte dépassée',
    '56': 'Carte absente du fichier',
    '57': 'Transaction non permise à ce porteur',
    '58': 'Transaction interdite au terminal',
    '59': 'Suspicion de fraude',
    '60': 'L\'accepteur de carte doit contacter l\'acquéreur',
    '61': 'Dépasse la limite du montant de retrait',
    '63': 'Règles de sécurité non respectées',
    '68': 'Réponse non parvenue ou reçue trop tard',
    '90': 'Arrêt momentané du système',
    '91': 'Emetteur de cartes inaccessible',
    '96': 'Mauvais fonctionnement du système',
    '97': 'Échéance de la temporisation de surveillance globale',
    '98': 'Serveur indisponible routage réseau demandé à nouveau',
    '99': 'Incident domaine initiateur',
}
