FIELD_GLOSSARY = {
    "license id": (
        "License ID",
        "Identifiant unique de la licence au format XX-X-XX-XXXXXX (ex: EU-A-A1-000003). "
        "Encode la région (EU/US), le dépôt et le sous-dépôt."
    ),
    "license key": (
        "License Key",
        "Clé d'activation de la licence au format XXXX-XXXX-XXXX-XXXX. Utilisée pour activer le logiciel."
    ),
    "status": (
        "Status",
        "État courant de la licence. Valeurs : Active, Expired, Pending Renewal, Revoked, Suspended, Under Review."
    ),
    "risk rating": (
        "Risk Rating",
        "Niveau de risque de la licence, de Low à Critical. "
        "Valeurs : Critical > High > Medium-High > Medium > Low. "
        "Évalué selon la criticité des données traitées, la conformité et l'exposition réglementaire."
    ),
    "tier": (
        "Tier",
        "Offre commerciale souscrite. Valeurs (ordre croissant) : Free < Starter < Professional < Business < Enterprise < Unlimited. "
        "Détermine le nombre de sièges, les fonctionnalités et le niveau de support."
    ),
    "compliance level": (
        "Compliance Level",
        "Niveau de conformité réglementaire atteint. "
        "Valeurs : Level 1 - Basic < Level 2 - Standard < Level 3 - Enhanced < Level 4 - Premium < Level 5 - Enterprise."
    ),
    "sla level": (
        "SLA Level",
        "Niveau de contrat de service (Service Level Agreement). "
        "Valeurs (ordre croissant) : Bronze < Silver < Gold < Platinum < Diamond. "
        "Détermine les garanties de disponibilité, les heures de support et les délais de réponse."
    ),
    "gdpr compliance status": (
        "GDPR Compliance Status",
        "Statut de conformité au règlement européen GDPR. "
        "Valeurs : Fully Compliant, Partially Compliant, Non-Compliant, Under Assessment, Remediation In Progress."
    ),
    "payment status": (
        "Payment Status",
        "État du paiement de la licence. Valeurs : Paid, Pending, Overdue, Partial, Waived."
    ),
    "audit result": (
        "Audit Result",
        "Résultat du dernier audit de conformité. "
        "Valeurs : Pass, Conditional Pass, Pass with Observations, Fail - Minor, Fail - Major, Pending."
    ),
    "license type": (
        "License Type",
        "Type de licence selon la technologie et la réglementation. "
        "Ex : GDPR Compliant - Software, Software - Cloud SaaS, Software - API, Hardware - *, CE Marked - *."
    ),
    "license category": (
        "License Category",
        "Catégorie interne de classification : A, B, C ou D. "
        "Correspond au dépôt principal (A → EU-Repo-A, etc.)."
    ),
    "uptime guarantee": (
        "Uptime Guarantee (%)",
        "Pourcentage de disponibilité garantie par le SLA. Ex : 99.9% signifie moins de 8h d'indisponibilité par an."
    ),
    "support hours": (
        "Support Hours",
        "Plage horaire de support technique disponible. Ex : 24x7 (24h/24, 7j/7), 16x7, 12x5, 8x5."
    ),
    "renewal frequency": (
        "Renewal Frequency",
        "Fréquence de renouvellement de la licence. Valeurs : Monthly, Quarterly, Semi-Annual, Annual, Biennial, Perpetual."
    ),
    "auto-renew": (
        "Auto-Renew",
        "Indique si la licence se renouvelle automatiquement à expiration. Valeurs : Yes / No."
    ),
    "cancellation notice": (
        "Cancellation Notice (Days)",
        "Préavis minimum en jours pour résilier la licence avant son renouvellement automatique."
    ),
    "seats licensed": (
        "Seats Licensed",
        "Nombre de sièges (utilisateurs) autorisés par la licence."
    ),
    "seats used": (
        "Seats Used",
        "Nombre de sièges actuellement utilisés. À comparer à Seats Licensed pour évaluer le taux d'utilisation."
    ),
    "annual fee": (
        "Annual Fee / Annual Fee (USD)",
        "Montant annuel facturé pour la licence. En devise locale pour les licences EU, en USD pour les licences US."
    ),
    "payment method": (
        "Payment Method",
        "Mode de paiement utilisé. Ex : Invoice Net-30, PayPal, ACH, Credit Card, Bank Transfer."
    ),
    "data residency": (
        "Data Residency",
        "(EU uniquement) Localisation géographique où les données sont stockées. "
        "Ex : EU Only, EU + UK, Global with EU Primary, Specific Country."
    ),
    "cross-border transfer": (
        "Cross-Border Transfer",
        "(EU uniquement) Statut des transferts de données hors UE. "
        "Valeurs : Allowed - Adequacy, Allowed - SCCs, Pending Assessment, Prohibited."
    ),
    "encryption standard": (
        "Encryption Standard",
        "(EU uniquement) Standard de chiffrement des données utilisé. Ex : TLS 1.3, AES-256-GCM, AES-128-GCM, ChaCha20."
    ),
    "audit frequency": (
        "Audit Frequency",
        "Fréquence des audits de conformité : Monthly, Quarterly, Semi-Annual, Annual."
    ),
    "data protection officer": (
        "Data Protection Officer / DPO",
        "(EU uniquement) Nom et email du délégué à la protection des données (DPO), "
        "responsable de la conformité GDPR au sein de la société titulaire."
    ),
    "ce marking": (
        "CE Marking",
        "(EU uniquement) Indique si le produit porte le marquage CE (conformité aux normes européennes). Valeurs : Yes / No."
    ),
    "environmental compliance": (
        "Environmental Compliance",
        "(EU uniquement) Normes environnementales respectées. Ex : RoHS, REACH, EU-US Data Privacy Framework."
    ),
    "ip address bound": (
        "IP Address Bound",
        "Adresse IP à laquelle la licence est liée. La licence n'est valable que depuis cette IP."
    ),
    "mac address bound": (
        "MAC Address Bound",
        "Adresse MAC du matériel auquel la licence est liée."
    ),
    "software version": (
        "Software Version",
        "Version du logiciel couverte par la licence."
    ),
    "department": (
        "Department",
        "Service interne de l'entreprise titulaire de la licence. "
        "Ex : IT, HR, Finance, Engineering, Legal, Marketing, Operations, R&D, Security."
    ),
    "approved by": (
        "Approved By",
        "Nom de la personne qui a approuvé l'émission de la licence."
    ),
    "issue date": (
        "Issue Date",
        "Date d'émission (création) de la licence."
    ),
    "expiration date": (
        "Expiration Date",
        "Date d'expiration de la licence. Après cette date, le statut passe à Expired."
    ),
    "last renewed": (
        "Last Renewed",
        "Date du dernier renouvellement de la licence."
    ),
    "next review date": (
        "Next Review Date",
        "Date prévue pour la prochaine révision de la licence (audit, renouvellement ou mise à jour)."
    ),
    "repository": (
        "Repository",
        "Dépôt principal auquel appartient la licence. Ex : EU-Repo-A, US-Repo-B."
    ),
    "sub-repository": (
        "Sub-Repository",
        "Sous-dépôt de classification interne. Ex : A1, B2, C3."
    ),
    "vat number": (
        "VAT Number",
        "(EU uniquement) Numéro de TVA intracommunautaire de la société titulaire."
    ),
    "hash signature": (
        "Hash Signature",
        "Empreinte cryptographique (MD5) de la licence, utilisée pour vérifier son intégrité."
    ),
    "internal reference": (
        "Internal Reference",
        "Référence interne au format REF-XXXXX, utilisée pour le suivi dans les systèmes internes."
    ),
    "invoice number": (
        "Invoice Number",
        "Numéro de facture associé à la licence. Format : INV-EU-XXXXXX ou INV-US-XXXXXX."
    ),
    "data classification": (
        "Data Classification",
        "(US uniquement) Niveau de classification des données traitées. "
        "Ex : Public, Internal, Confidential, Restricted."
    ),
    "encryption required": (
        "Encryption Required",
        "(US uniquement) Indique si le chiffrement des données est obligatoire pour cette licence."
    ),
}

# aliases : mots-clés de la question → clé dans FIELD_GLOSSARY
GLOSSARY_ALIASES = {
    "risque": "risk rating",
    "risk": "risk rating",
    "rating": "risk rating",
    "sla": "sla level",
    "niveau de service": "sla level",
    "compliance level": "compliance level",
    "conformité": "compliance level",
    "gdpr": "gdpr compliance status",
    "rgpd": "gdpr compliance status",
    "statut": "status",
    "état": "status",
    "offre": "tier",
    "plan": "tier",
    "siège": "seats licensed",
    "seats": "seats licensed",
    "utilisateurs": "seats licensed",
    "renouvellement": "renewal frequency",
    "renewal": "renewal frequency",
    "résiliation": "cancellation notice",
    "préavis": "cancellation notice",
    "cancellation": "cancellation notice",
    "uptime": "uptime guarantee",
    "disponibilité": "uptime guarantee",
    "dpo": "data protection officer",
    "délégué": "data protection officer",
    "chiffrement": "encryption standard",
    "encryption": "encryption standard",
    "résidence": "data residency",
    "residency": "data residency",
    "transfert": "cross-border transfer",
    "transfer": "cross-border transfer",
    "audit result": "audit result",
    "résultat audit": "audit result",
    "marquage ce": "ce marking",
    "environnement": "environmental compliance",
    "tva": "vat number",
    "vat": "vat number",
    "frais": "annual fee",
    "fee": "annual fee",
    "tarif": "annual fee",
    "prix": "annual fee",
    "paiement": "payment status",
    "payment": "payment status",
    "ip": "ip address bound",
    "mac": "mac address bound",
    "version": "software version",
    "département": "department",
    "expiration": "expiration date",
    "expire": "expiration date",
    "émission": "issue date",
    "clé": "license key",
    "key": "license key",
    "hash": "hash signature",
    "signature": "hash signature",
    "référence": "internal reference",
    "facture": "invoice number",
    "invoice": "invoice number",
    "support hours": "support hours",
    "heures de support": "support hours",
}


def glossary_lookup(question: str) -> str:
    q = question.lower()
    matches: dict[str, tuple[str, str]] = {}

    for key, entry in FIELD_GLOSSARY.items():
        if key in q:
            matches[key] = entry

    for alias, key in GLOSSARY_ALIASES.items():
        if alias in q and key not in matches:
            matches[key] = FIELD_GLOSSARY[key]

    if not matches:
        return ""

    return "\n\n".join(f"{name} :\n{desc}" for _, (name, desc) in matches.items())
