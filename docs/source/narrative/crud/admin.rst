.. _admin:

=====
Admin
=====

.. contents:: :local:

Introduction
============

Admin, or administration interface, provides super administrator capabilities for your Websauna site. You can easily browse, add and edit data without need to write explicit forms and views or install additional software for database browsing.

Admin is accessible for users who belong *admin* group. The first signed up user is automatically added to this group. Different permissions schemes can be implemented through ACL, so that groups of people can only view partial data or cannot modify it.

Admin is automatically generated for your data :doc:`models <../modelling/models>`. It is based on Websauna :doc:`CRUD <./crud>` and :doc:`automatic form generation <../form/autoform>`.


.. image:: ../images/admin.png
    :width: 640px

Getting started
===============

How to get your models to admin is :doc:`covered in tutorial <../../tutorials/gettingstarted/index>`.

Creating an model admin
=======================

Model admin provides automatic :term:`CRUD` for your :term:`SQLAlchemy` modelled data.

First you have created a model in ``models.py``.

Then create a model admin binding in ``admins.py`` module of your project.

.. code-block:: python

    from pyramid.security import Deny, Allow, Everyone
    from websauna.system.admin.modeladmin import ModelAdmin, model_admin
    from websauna.system.crud import Base64UUIDMapper

    from .models import UserOwnedAccount
    from .models import Asset


    @model_admin(traverse_id="user-accounts")
    class UserAccountAdmin(ModelAdmin):
        """Manage user owned accounts and their balances."""

        # Set permissions so that this information can be only shown,
        # never edited or deleted. If we don't set any permissions
        # default admin permissions from the admin root object are inherited.
        __acl__ = {
            (Deny, Everyone, 'add'),
            (Allow, 'group:admin', 'view'),
            (Deny, Everyone, 'edit'),
            (Deny, Everyone, 'delete'),
        }

        title = "Users' accounts"

        singular_name = "user-account"
        plural_name = "user-accounts"
        model = UserOwnedAccount

        # UserOwnedAccount.id attribute is uuid type
        mapper = Base64UUIDMapper(mapping_attribute="id")

        class Resource(ModelAdmin.Resource):

            # Get something human readable about this object to the breadcrumbs bar
            def get_title(self):
                return self.get_object().user.friendly_name + ": " + self.get_object().account.asset.name

Make sure ``admins.py`` is scanned in your :py:class:`websauna.system.Initializer` of your application. This should happen by default with your Websauna application scaffold.

.. code-block:: python

    def configure_model_admins(self):
        """Register the models of this application."""

        # Call parent which registers user and group admins
        super(Initializer, self).configure_model_admins()

        # Scan our admins
        from . import admins
        self.config.scan(admins)

Now we can see the first peak on the model admin:

.. image-source:: ../images/model-admin-1.png
    :width: 640px

The default listing view output is still messy, because the listing view doesn't know what columns to show. Let's fix this. Let's create a new file ``adminviews.py``:

.. code-block:: python

    from websauna.system.admin.utils import get_admin_url_for_sqlalchemy_object
    from websauna.system.crud import listing
    from websauna.system.http import Request
    from websauna.viewconfig import view_overrides
    from websauna.system.admin.views import Listing as DefaultListing
    from websauna.system.admin.views import Show as DefaultShow
    from websauna.wallet.models import UserOwnedAccount
    from websauna.wallet.utils import get_asset_formatter

    from . import admins


    def get_user_for_account(view, column, user_owned_account: UserOwnedAccount):
        """Show user name."""
        return user_owned_account.user.friendly_name


    def get_asset_for_account(view, column, user_owned_account: UserOwnedAccount):
        """Show the name of the asset user is owning."""
        return user_owned_account.account.asset.name


    def get_amount_for_account(view, column, user_owned_account: UserOwnedAccount):
        """Format asset amount using a custom formatter, picked by asset type."""
        asset = user_owned_account.account.asset
        # Return a string like "{.2f}"
        formatter = get_asset_formatter(asset.asset_format)
        return formatter.format(user_owned_account.account.denormalized_balance)


    def get_user_admin_link(request: Request, resource: admins.UserAccountAdmin.Resource):
        """Get link to a user admin show view from the user owned account."""
        user_account = resource.get_object()
        user = user_account.user
        admin = resource.get_admin()
        return get_admin_url_for_sqlalchemy_object(admin, user, "show")


    @view_overrides(context=admins.UserAccountAdmin)
    class UserAccountListing(DefaultListing):
        """User listing modified to show the user hometown based on geoip of last login IP."""
        table = listing.Table(
            columns = [
                listing.Column("id", "Id",),
                listing.Column("user", "Owner", getter=get_user_for_account, navigate_url_getter=get_user_admin_link),
                listing.Column("asset", "Asset", getter=get_asset_for_account),
                listing.Column("amount", "Amount", getter=get_amount_for_account),
                listing.ControlsColumn()
            ]
        )


Now listing view looks better:

.. image:: ../images/model-admin-2.png
    :width: 640px

However the show view is still gibberish and does not give us any information:

.. image:: ../images/model-admin-2.png
    :width: 640px

Let's also fix that by adding a new class in ``adminviews.py``:

.. code-block:: python

    TODO

Creating an admin view
======================

Below is instructions how to create your own admin views. We use a view called *phone order* as an example.

Create a Pyramid traversal view and register it against Admin context. First we create a stub ``phoneorder.py``::

    from pyramid.view import view_config

    from websauna.system.admin import Admin

    @view_config(context=Admin, name="phone-order", route_name="admin", permission="edit", renderer="admin/phone_order.html")
    def phone_order(context, request):
        return {}

In your Initializer make sure the module where you view lies is scanned::

    class Initializer:

        ...

        def config_admin(self):
            super(Initializer, self).config_admin()
            from . import phoneorder
            self.config.scan(phoneorder)

In the template ``phone_order.html``:

.. code-block:: html+jinja

    {% extends "admin/base.html" %}

    {% block admin_content %}
    <p>Content goes here...</p>
    {% endblock %}


Then you can later get the link to this page in template code:

.. code-block:: html+jinja

    <p>
        <a href="{{ request.resource_url(admin, 'phone-order') }}>Create phone order</a>
    </p>

Linking into the admin views of a model
=======================================

Preface: You have an SQLAlchemy object and you want to provide the link to its admin interface: show, edit or custom action.

To construct a link to the model instance inside admin interface, you need to

* Get a hold of the current admin object

* Ask admin to provide traversable resource for this object

* Use ``request.resource_url()`` to get the link

Example::

    # Get traversable resource for a model instance
    resource = request.admin.get_admin_resource(user)

    # Get a context view named "edit" for this resource
    edit_link = request.resource_url(resource, "edit")

Creating an admin panel
=======================

Panel shows summary information about one model on the landing page of the admin (dashboard).

Below is an example how one can customize this panel. We use ``UserOwnedAccount`` model in this example.

.. image:: ../images/panel.png
    :width: 640px

First create ``panels.py``:

.. code-block:: python

    import sqlalchemy
    from collections import OrderedDict
    from pyramid_layout.panel import panel_config
    from websauna.wallet.models import Account, UserOwnedAccount, Asset
    from websauna.wallet.utils import format_asset_amount

    from . import admins


    @panel_config(name='admin_panel', context=admins.UserAccountAdmin, renderer='admin/user_owned_account_panel.html')
    def user_owned_account(context, request):
        """Admin panel for Users."""

        dbsession = request.dbsession

        # Query all liabilities

        # NOTE: This is a bad SQLAlchemy example as this performances one query
        # per one asset. One could perform this with a single group by query

        liabilities = OrderedDict()
        account_summer = sqlalchemy.func.sum(Account.denormalized_balance).label("denormalized_balance")

        for asset in dbsession.query(Asset).order_by(Asset.name.asc()):
            total_balances = dbsession.query(account_summer).filter(Account.asset == asset).join(UserOwnedAccount).all()
            balance = total_balances[0][0]
            liabilities[asset.name] = format_asset_amount(balance, asset.asset_format)

        # These need to be passed to base panel template,
        # so it knows how to render buttons
        model_admin = context

        return locals()

Make sure you scan ``panels.py`` in your :py:class:`websauna.system.Initializer`:

.. code-block:: python


    def configure_model_admins(self):
        from . import panels
        self.config.scan(panels)

Create a matching template, ``admin/user_owned_account_panel.html`` in our case:

.. code-block:: html+jinja

    {% extends "admin/model_panel.html" %}

    {% block panel_title %}
    Users' accounts and balances
    {% endblock %}

    {% block panel_content %}
      <h3>Liabilities</h3>
      <table class="table">
        {% for name, amount in liabilities.items() %}
          <tr>
            <th>
              {{ name }}
            </th>

            <td>
              {{ amount }}
            </td>
          </tr>
        {% endfor %}
      </table>
    {% endblock panel_content %}

.. _override-listing:

Overriding an existing model admin
==================================

Here is an example how we override the existing model admin for the user. Then we enhance the admin functionality by overriding a listing view to show the city of the user based on the location of the last login IP address.

This is done using `pygeoip library <https://pypi.python.org/pypi/pygeoip/>`_.

First let's add our admin definition in ``admins.py``. Because this module is scanned after the stock :py:mod:`websauna.system.user.admins` it takes the precendence.

``admins.py``:

.. code-block:: python

    from websauna.system.admin.modeladmin import model_admin
    from websauna.system.user.admins import UserAdmin as _UserAdmin


    # Override default user admin
    @model_admin(traverse_id="user")
    class UserAdmin(_UserAdmin):

        class Resource(_UserAdmin.Resource):
            pass

Then we roll out our custom ``adminviews.py`` where we override listing view for user model admin.

``adminviews.py``:

.. code-block:: python

    import os
    import pygeoip

    from websauna.system.crud import listing
    from websauna.viewconfig import view_overrides
    from websauna.system.user import adminviews as _adminviews

    # Import local admin
    from . import admins


    _geoip = None

    def _get_geoip():
        """Lazily load geoip database to memory as it's several megabytes."""
        global _geoip
        if not _geoip:
            _geoip = pygeoip.GeoIP(os.path.join(os.path.dirname(__file__), '..', 'geoip.dat'), flags=pygeoip.MMAP_CACHE)
        return _geoip



    def get_location(view, column, user):
        """Get state from IP using pygeoip."""

        geoip = _get_geoip()

        ip = user.last_login_ip
        if not ip:
            return ""
        r = geoip.record_by_addr(ip)
        if not r:
            return ""

        code = r.get("metro_code", "")
        if code:
            return code

        code = (r.get("country_code") or "") + " " + (r.get("city") or "")
        return code


    @view_overrides(context=admins.UserAdmin)
    class UserListing(_adminviews.UserListing):
        """User listing modified to show the user hometown based on geoip of last login IP."""
        table = listing.Table(
            columns = [
                listing.Column("id", "Id",),
                listing.Column("friendly_name", "Friendly name"),
                listing.Column("location", "Location", getter=get_location),
                listing.ControlsColumn()
            ]
        )

And as a last action we scan our ``adminviews`` module in our initializer:

.. code-block:: python

    def run(self):
        super(Initializer, self).run()

        # ...

        from . import adminviews
        self.config.scan(adminviews)

This is how it looks like:

.. image:: ../images/geoip.png
    :width: 640px

Customizing admin layout
========================

Admin has its :ref:`own separate base template <template-admin/base.html>`. You can override it for total admin customization.

Below is an example using `Light Bootstrap Dashboard <http://www.creative-tim.com/product/light-bootstrap-dashboard>`_ template by Creative Tim (non-free).

.. image:: ../images/custom_admin.png
    :width: 640px

``admin/base.html``:

.. code-block:: html+jinja

    {% extends "site/base.html" %}

    {% block css %}

      <link rel="stylesheet" href="{{ 'websauna.system:static/bootstrap.min.css'|static_url }}">
      <link rel="stylesheet" href="{{ 'wattcoin:static/admin/assets/css/light-bootstrap-dashboard.css'|static_url }}">
      <link href="http://maxcdn.bootstrapcdn.com/font-awesome/4.2.0/css/font-awesome.min.css" rel="stylesheet">
      <link href='http://fonts.googleapis.com/css?family=Roboto:400,700,300' rel='stylesheet' type='text/css'>
      <link href="assets/css/pe-icon-7-stroke.css" rel="stylesheet"/>

      {# Include CSS for widgets #}
      {% if request.on_demand_resource_renderer %}
        {% for css_url in request.on_demand_resource_renderer.get_resources("css") %}
          <link rel="stylesheet" href="{{ css_url }}"></link>
        {% endfor %}
      {% endif %}

    {% endblock %}

    {% block header %}
    {% endblock %}

    {% block main %}
      <div class="wrapper">
        <div class="sidebar" data-color="purple" data-image="assets/img/sidebar-5.jpg">

          <!--

              Tip 1: you can change the color of the sidebar using: data-color="blue | azure | green | orange | red | purple"
              Tip 2: you can also add an image using data-image tag

          -->

          <div class="sidebar-wrapper">
            <div class="logo">
              <a href="{{ 'home'|route_url }}" class="simple-text">
                {{ site_name }}
              </a>
            </div>

            {% include "admin/sidebar.html" %}
          </div>
        </div>

        <div class="main-panel">
          <nav class="navbar navbar-default navbar-fixed">
            <div class="container-fluid">
              <div class="navbar-header">
                <button type="button" class="navbar-toggle" data-toggle="collapse" data-target="#navigation-example-2">
                  <span class="sr-only">Toggle navigation</span>
                  <span class="icon-bar"></span>
                  <span class="icon-bar"></span>
                  <span class="icon-bar"></span>
                </button>
                <a class="navbar-brand" href="#">Dashboard</a>
              </div>
              <div class="collapse navbar-collapse">
                <ul class="nav navbar-nav navbar-left">
                  <li>
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                      <i class="fa fa-dashboard"></i>
                    </a>
                  </li>
                  <li class="dropdown">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                      <i class="fa fa-globe"></i>
                      <b class="caret"></b>
                      <span class="notification">5</span>
                    </a>
                    <ul class="dropdown-menu">
                      <li><a href="#">Notification 1</a></li>
                      <li><a href="#">Notification 2</a></li>
                      <li><a href="#">Notification 3</a></li>
                      <li><a href="#">Notification 4</a></li>
                      <li><a href="#">Another notification</a></li>
                    </ul>
                  </li>
                  <li>
                    <a href="">
                      <i class="fa fa-search"></i>
                    </a>
                  </li>
                </ul>

                <ul class="nav navbar-nav navbar-right">
                  <li>
                    <a href="">
                      Account
                    </a>
                  </li>
                  <li class="dropdown">
                    <a href="#" class="dropdown-toggle" data-toggle="dropdown">
                      Dropdown
                      <b class="caret"></b>
                    </a>
                    <ul class="dropdown-menu">
                      <li><a href="#">Action</a></li>
                      <li><a href="#">Another action</a></li>
                      <li><a href="#">Something</a></li>
                      <li><a href="#">Another action</a></li>
                      <li><a href="#">Something</a></li>
                      <li class="divider"></li>
                      <li><a href="#">Separated link</a></li>
                    </ul>
                  </li>
                  <li>
                    <a href="#">
                      Log out
                    </a>
                  </li>
                </ul>
              </div>
            </div>
          </nav>


          <div class="content">
            <div class="container-fluid">
              {% block content %}

                {{ context|admin_breadcrumbs|safe }}

                {% block admin_content %}
                {% endblock admin_content %}

                {% block crud_content %}
                {% endblock crud_content %}

              {% endblock content %}

            </div>
          </div>


          <footer class="footer">
            <div class="container-fluid">
              <p class="copyright pull-right">
                &copy; {{ now().year }} {{ site_author }}
              </p>
            </div>
          </footer>

        </div>
      </div>
    {% endblock %}

    {% block footer %}

    {% endblock %}

    {% block custom_script %}
      <script src="{{ 'websauna.system:static/admin.js'|static_url }}"></script>
    {% endblock %}

The custom sidebar pulls the contents of *Data* admin menu:

.. code-block:: html+jinja

    <ul class="nav">
      <li>
        <a href="{{ 'admin_home'|route_url }}">
          <i class="pe-7s-graph"></i>
          <p>Dashboard</p>
        </a>
      </li>

      {% with entries=request.admin.get_admin_menu().get_entry("admin-menu-data").submenu.get_entries() %}
        {% for entry in entries %}
          <li>
            <a href="{{ entry.get_link(request) }}">
              {{ entry.label }}
            </a>
          </li>
        {% endfor %}
      {% endwith %}
    </ul>