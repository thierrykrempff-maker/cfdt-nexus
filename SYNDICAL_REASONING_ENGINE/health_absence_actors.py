"""Competence boundaries for health, absence and social-protection actors."""

from __future__ import annotations

from .health_absence_models import ActorResponsibility, CompetentActor


def health_actor_policy() -> tuple[ActorResponsibility, ...]:
    rows = (
        (CompetentActor.EMPLOYEE, ("transmettre les justificatifs nécessaires", "signaler les difficultés"), ("auto-qualifier une reconnaissance administrative",)),
        (CompetentActor.EMPLOYER, ("recevoir les justificatifs", "organiser la reprise et le reclassement", "traiter le contrat"), ("poser un diagnostic", "décider à la place de la CPAM")),
        (CompetentActor.HR, ("tracer les transmissions", "coordonner les démarches internes"), ("interpréter médicalement un avis",)),
        (CompetentActor.PAYROLL, ("traiter les éléments de paie", "expliquer une régularisation"), ("reconnaître un accident professionnel",)),
        (CompetentActor.CPAM, ("instruire et décider le caractère professionnel", "traiter les IJSS"), ("rendre un avis d'aptitude au poste",)),
        (CompetentActor.TREATING_DOCTOR, ("établir les documents relevant de sa compétence médicale",), ("organiser le reclassement",)),
        (CompetentActor.OCCUPATIONAL_PHYSICIAN, ("rendre les avis relevant de la santé au travail", "proposer des aménagements"), ("calculer les droits de paie",)),
        (CompetentActor.MEDICAL_ADVISER, ("intervenir dans le champ médico-administratif de l'assurance maladie",), ("prendre une décision employeur",)),
        (CompetentActor.LABOUR_INSPECTORATE, ("intervenir dans son champ de contrôle et d'information",), ("rendre un avis médical ou une décision CPAM",)),
        (CompetentActor.PROVIDENT_BODY, ("appliquer les garanties contractuelles après instruction",), ("promettre une prise en charge avant instruction",)),
        (CompetentActor.MUTUAL_INSURER, ("gérer affiliation, dispense ou portabilité selon le contrat",), ("décider une inaptitude",)),
        (CompetentActor.INSURER, ("instruire les garanties relevant du contrat d'assurance",), ("garantir une prise en charge avant instruction",)),
        (CompetentActor.AGIRC_ARRCO, ("traiter les droits relevant de la retraite complémentaire",), ("gérer les IJSS",)),
        (CompetentActor.URSSAF, ("documenter les règles de cotisations publiques",), ("arbitrer un litige médical",)),
        (CompetentActor.CSE, ("être consulté lorsque la règle l'exige", "agir dans ses attributions"), ("accéder aux détails médicaux non nécessaires",)),
        (CompetentActor.DISABILITY_OFFICER, ("faciliter l'orientation et les aménagements dans son champ",), ("accéder à un diagnostic non nécessaire",)),
        (CompetentActor.UNION_REPRESENTATIVE, ("accompagner", "vérifier", "documenter", "intervenir"), ("poser un diagnostic", "promettre un droit")),
        (CompetentActor.LEGAL_COUNSEL, ("évaluer les recours et délais",), ("se substituer aux autorités médicales ou administratives",)),
    )
    return tuple(ActorResponsibility(actor, duties, prohibited) for actor, duties, prohibited in rows)
