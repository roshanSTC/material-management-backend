
from app.models.project import Project


class AttachmentAuthorizationError(Exception):
    pass


def authorize_project_access(
    *,
    user_id: int,
    project_id: int,
) -> Project:
    """
    Verify that the user is allowed to access the project.

    Returns the project when access is allowed.
    Raises AttachmentAuthorizationError otherwise.
    """

    project = Project.query.filter(
        Project.id == project_id
    ).first()

    if project is None:
        raise AttachmentAuthorizationError(
            "Project not found."
        )

    # ---------------------------------------------------------
    # TODO:
    # Add your application's actual project-level permission
    # logic here once the user/project authorization rules are
    # finalized.
    #
    # For example:
    #
    # if not user_can_access_project(user_id, project):
    #     raise AttachmentAuthorizationError(
    #         "You do not have access to this project."
    #     )
    # ---------------------------------------------------------

    return project
