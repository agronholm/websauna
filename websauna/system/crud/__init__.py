"""An abstract CRUD implementation based on traversal. The default support for SQLAlchemy and Deform."""

from abc import abstractmethod
from websauna.system.core.traversal import Resource as _Resource

from .urlmapper import Base64UUIDMapper


class Resource(_Resource):
    """One object in CRUD traversing.

    Maps the raw database object under CRUD view/edit/delete control to traverse path.

    Presents an underlying model instance mapped to an URL path. ``__parent__`` attribute points to a CRUD instance.
    """

    def __init__(self, obj:object):
        """
        :param obj: The underlying object we wish to wrap for travering.
        """
        self.obj = obj

    def get_object(self) -> object:
        """Return the wrapped database object."""
        return self.obj

    def get_path(self):
        """Extract the traverse path name from the database object."""
        assert hasattr(self, "__parent__"),  "get_path() can be called only for objects whose lineage is set by make_lineage()"

        crud = self.__parent__
        path = crud.mapper.get_path_from_object(self.obj)
        return path

    def get_model(self) -> type:
        """Get the model class represented by this resource."""
        return self.__parent__.get_model()

    def get_title(self) -> str:
        """Title used on view, edit, delete, pages.

        By default use the capitalized URL path path.
        """
        return self.get_path()


class CRUD(_Resource):
    """Define create-read-update-delete interface for an model.

    We use Pyramid traversing to get automatic ACL permission support for operations. As long given CRUD resource parts define __acl__ attribute, permissions are respected automatically.

    URLs are the following:

        List: $base/listing

        Add: $base/add

        Show $base/$id/show

        Edit: $base/$id/edit

        Delete: $base/$id/delete
    """

    # How the model is referred in templates. e.g. "User"
    title = "xx"

    # TODO: This is inperfect directly copied from Django - many languages have more plural forms than two. Fix when i18n lands
    #: Helper noun used in the default placeholder texts
    singular_name = "item"

    # TODO: This is inperfect directly copied from Django - many languages have more plural forms than two. Fix when i18n lands
    #: Helper noun used in the default placeholder texts
    plural_name = "items"

    #: Mapper defines how objects are mapped to URL space. The default mapper assumes models have attribute ``uuid`` which is base64 encoded to URL. You can change this to :py:class:`websauna.system.crud.urlmapper.IdMapper` if you instead to want to use ``id`` as a running counter primary column in URLs. This is not recommended in security wise, though.
    mapper = Base64UUIDMapper()

    def make_resource(self, obj) -> Resource:
        """Take raw model instance and wrap it to Resource for traversing.

        :param obj: SQLALchemy object or similar model object.
        :return: :py:class:`websauna.core.traverse.Resource`
        """

        # Use internal Resource class to wrap the object
        if hasattr(self, "Resource"):
            return self.Resource(obj)

        raise NotImplementedError("Does not know how to wrap to resource: {}".format(obj))

    def wrap_to_resource(self, obj) -> Resource:
        # Wrap object to a traversable part
        instance = self.make_resource(obj)

        path = self.mapper.get_path_from_object(obj)
        assert type(path) == str, "Object {} did not map to URL path correctly, got path {}".format(obj, path)
        instance.make_lineage(self, instance, path)
        return instance

    def traverse_to_object(self, path) -> Resource:
        """Wraps object to a traversable URL.

        Loads raw database object with id and puts it inside ``Instance`` object,
         with ``__parent__`` and ``__name__`` pointers.
        """

        # First try if we get an view for the current instance with the name
        id = self.mapper.get_id_from_path(path)
        obj = self.fetch_object(id)
        return self.wrap_to_resource(obj)

    @abstractmethod
    def fetch_object(self, id) -> object:
        """Load object from the database for CRUD path for view/edit/delete."""
        raise NotImplementedError("Please use concrete subclass like websauna.syste.crud.sqlalchemy")

    def get_object_url(self, obj, view_name=None) -> str:
        """Get URL for view for an object inside this CRUD.

        ;param request: HTTP request instance

        :param obj: Raw object, e.g. SQLAlchemy instance, which can be wrapped with ``wrap_to_resource``.

        :param view_name: Traverse view name for the resource. E.g. ``show``, ``edit``.
        """
        res = self.wrap_to_resource(obj)
        if view_name:
            return self.request.resource_url(res, view_name)
        else:
            return self.request.resource_url(res)

    def __getitem__(self, path) -> Resource:
        """Traverse to a model instance.

        :param path: Part of URL which is resolved to an object via ``mapper``.
        """

        if self.mapper.is_id(path):
            return self.traverse_to_object(path)
        else:
            # Signal that this id is not part of the CRUD database and may be a view
            raise KeyError



