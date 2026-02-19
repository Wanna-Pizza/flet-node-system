
# Creating an Extension


 Summarize

While** **[Flet controls](https://docs.flet.dev/controls/) leverage many built-in** **[Flutter widgets](https://docs.flutter.dev/ui/widgets) to enable the creation of complex applications, not all Flutter widgets or third-party packages can be directly supported by the Flet team or included in the core Flet framework. At the same time, the Flutter ecosystem is vast and offers developers a wide range of possibilities to extend functionality beyond the core.

To address this, the Flet framework provides an extensibility mechanism. This allows you to incorporate widgets and APIs from your own custom Flutter packages or** **[third-party libraries](https://pub.dev/packages?sort=popularity) directly into your Flet application.

In this guide, you will learn how to create Flet extension from template and then customize it to integrate 3 ^rd^ -party Flutter package into your Flet app.

### Prerequisites[#](https://docs.flet.dev/extend/user-extensions/#prerequisites "Permanent link")

To integrate custom Flutter package into Flet you need to have basic understanding of how to create Flutter apps and packages in Dart language and have Flutter development environment configured. See** **[Flutter Getting Started](https://docs.flutter.dev/get-started/install)for more information about Flutter and Dart.

## Create Flet extension from template[#](https://docs.flet.dev/extend/user-extensions/#create-flet-extension-from-template "Permanent link")

Flet now makes it easy to create and build projects with your custom controls based on Flutter widgets or Flutter 3 ^rd^ -party packages. In the example below, we will be creating a custom Flet extension based on the** **[flutter_spinkit](https://pub.dev/packages/flutter_spinkit) package.

**Step 1.** Create new virtual environment and** **[install Flet](https://docs.flet.dev/getting-started/installation/) there.

**Step 2.** Create new extension project from template.

```
flet create --template extension --project-name flet-spinkit
```

A project with new FletSpinkit control will be created. The control is just a Flutter Text widget with text property, which we will customize later.

**Step 3.** Build example app.

Flet project created from extension template has** **`examples/flet_spinkit_example` folder with the example app.

When in the folder where your** **`pyproject.toml` for the app is (`examples/flet_spinkit_example`), run** **`flet build` command, for example, for macos:

Open the app and see the new custom Flet Control:

```
open build/macos/flet-spinkit-example.app
```

[![](https://docs.flet.dev/assets/extensions/example.png)](https://docs.flet.dev/assets/extensions/example.png)

#### Change Python files[#](https://docs.flet.dev/extend/user-extensions/#change-python-files "Permanent link")

Once the project was built for desktop once, you can make changes to your python files and run it without rebuilding.

First, if you are not using uv, install dependencies from pyproject.toml:

orNow you can make changes to your example app main.py:

```
importfletasft

fromflet_spinkitimport FletSpinkit


defmain(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(
        ft.Container(
            height=150,
            width=300,
            alignment=ft.alignment.center,
            bgcolor=ft.Colors.PINK_200,
            content=FletSpinkit(
                tooltip="My new PINK FletSpinkit Control tooltip",
                value="My new PINK FletSpinkit Flet Control",
            ),
        ),
    )


ft.run(main)
```

and run:

[![](https://docs.flet.dev/assets/extensions/example-pink.png)](https://docs.flet.dev/assets/extensions/example-pink.png)

#### Change Flutter package[#](https://docs.flet.dev/extend/user-extensions/#change-flutter-package "Permanent link")

When you make any changes to your flutter package, you need to rebuild:

If you need to debug, run this command:

```
build/macos/flet-spinkit-example.app/Contents/MacOS/flet-spinkit-example --debug
```

## Integrate 3 ^rd^ -party Flutter package[#](https://docs.flet.dev/extend/user-extensions/#integrate-3rd-party-flutter-package "Permanent link")

Let's integrate** **[flutter_spinkit](https://pub.dev/packages/flutter_spinkit) package into our Flet app.

**Step 1.** Add dependency

Go to** **`src/flutter/flet_spinkit` folder and run this command to add dependency to** **`flutter_spinkit` to** **`pubspec.yaml`:

```
flutter pub add flutter_spinkit
```

Read more information about using Flutter packages** **[here](https://docs.flutter.dev/packages-and-plugins/using-packages).

**Step 2.** Modify** **`dart` file

In the** **`src/flutter/flet_spinkit/lib/src/flet_spinkit.dart` file, add import statement and replace Text widget with** **`SpinKitRotatingCircle`widget:

```
import'package:flet/flet.dart';
import'package:flutter/material.dart';
import'package:flutter_spinkit/flutter_spinkit.dart';

classFletSpinkitControlextendsStatelessWidget{
finalControlcontrol;

constFletSpinkitControl({
super.key,
requiredthis.control,
});

@override
Widgetbuild(BuildContextcontext){
WidgetmyControl=SpinKitRotatingCircle(color:Colors.red,size:100.0);

returnLayoutControl(control:control,child:myControl);
}
}
```

**Step 3.** Rebuild example app

Go to** **`examples/flet_spinkit_example`, clear cache and rebuild your app:

**Step 4.** Run your app

[![](https://docs.flet.dev/assets/extensions/spinkit1.gif)](https://docs.flet.dev/assets/extensions/spinkit1.gif)

## Flet extension structure[#](https://docs.flet.dev/extend/user-extensions/#flet-extension-structure "Permanent link")

After creating new Flet project from extension template, you will see the following folder structure:

```
├── LICENSE
├── mkdocs.yml
├── README.md
├── docs
│   └── index.md
│   └── FletSpinkit.md
├── examples
│   └── flet_spinkit_example
│       ├── README.md
│       ├── pyproject.toml
│       └── src
│           └── main.py
├── pyproject.toml
└── src
    ├── flet_spinkit
    │   ├── __init__.py
    │   └── flet_spinkit.py
    └── flutter
        └── flet_spinkit
            ├── CHANGELOG.md
            ├── LICENSE
            ├── README.md
            ├── lib
            │   ├── flet_spinkit.dart
            │   └── src
            │       ├── create_control.dart
            │       └── flet_spinkit.dart
            └── pubspec.yaml
```

Flet extension consists of: *** ** **package** , located in** **`src` folder *** ** **example app** , located in** **`examples/flet-spinkit_example` folder *** ** **docs** , located in** **`docs`folder

### Package[#](https://docs.flet.dev/extend/user-extensions/#package "Permanent link")

Package is the component that will be used in your app. It consists of two parts: Python and Flutter.

#### Python[#](https://docs.flet.dev/extend/user-extensions/#python "Permanent link")

##### flet_spinkit.py[#](https://docs.flet.dev/extend/user-extensions/#flet_spinkitpy "Permanent link")

Defines the Python-side Flet control.** **`FletSpinkit` is registered with** **`@ft.control("flet_spinkit")` and inherits from** **`ft.LayoutControl`, which ties it to the Flutter** **`Control.type` handled in the extension. The class currently includes a value: str property and a placeholder docstring.

#### Flutter[#](https://docs.flet.dev/extend/user-extensions/#flutter "Permanent link")

##### pubspec.yaml[#](https://docs.flet.dev/extend/user-extensions/#pubspecyaml "Permanent link")

Flutter package manifest for the extension. Declares SDK constraints and dependencies. Notable deps:

* `flet` for Flet extension APIs
* `flutter_spinkit` for the spinner widgets used by the control

##### flet_spinkit.dart[#](https://docs.flet.dev/extend/user-extensions/#flet_spinkitdart "Permanent link")

Library entrypoint. Exports the public** **`Extension` class from** **`extension.dart`.

##### src/extension.dart[#](https://docs.flet.dev/extend/user-extensions/#srcextensiondart "Permanent link")

Registers the extension with Flet.** **`Extension.createWidget` maps** **`Control.type` to the Flutter widget; currently maps "flet_spinkit" to FletSpinkitControl.

##### src/flet_spinkit.dart[#](https://docs.flet.dev/extend/user-extensions/#srcflet_spinkitdart "Permanent link")

Flutter wrapper widget for the control.** **`FletSpinkitControl` builds a** **`SpinKitRotatingCircle` and wraps it with** **`LayoutControl` so layout/state from the Python control are applied.

### Example app[#](https://docs.flet.dev/extend/user-extensions/#example-app "Permanent link")

##### src/main.py[#](https://docs.flet.dev/extend/user-extensions/#srcmainpy "Permanent link")

Python program that uses Flet Python control.

##### pyproject.toml[#](https://docs.flet.dev/extend/user-extensions/#pyprojecttoml "Permanent link")

Here you specify dependency to your package, which can be:

* **Path dependency**

Absolute path to your Flet extension folder, for example:

```
dependencies = [
  "flet-spinkit @ file:///Users/user-name/projects/flet-spinkit",
  "flet>=0.80.2",
]
```

* **Git dependency**

Link to git repository, for example:

```
dependencies = [
  "flet-ads @ git+https://github.com/flet-dev/flet-ads.git",
  "flet>=0.80.2",
]
```

* **PyPi dependency**

Name of the package published on pypi.org, for example:

```
dependencies = [
  "flet-ads",
  "flet>=0.80.2",
]
```

### Docs[#](https://docs.flet.dev/extend/user-extensions/#docs "Permanent link")

If you are planning to share your extension with community, you can easily generate documentation from your source code using** **[mkdocs](https://www.mkdocs.org/).

Flet extension comes with a** **`docs` folder containing initial files for your documentation and a** **`mkdocs.yml` file at the project root.

From the folder that contains** **`mkdocs.yml`, run the following command to see how your docs look locally:

Open** **[http://127.0.0.1:8000](http://127.0.0.1:8000/) in your browser:

[![](https://docs.flet.dev/assets/extensions/mkdocs.png)](https://docs.flet.dev/assets/extensions/mkdocs.png)

Once your documentation is ready, if your package is hosted on GitHub, your can run the following command to host your documentation on GitHub pages:

You may find** **[this guide](https://realpython.com/python-project-documentation-with-mkdocs/#step-5-build-your-documentation-with-mkdocs) helpful to get started with mkdocs.

## Customize properties[#](https://docs.flet.dev/extend/user-extensions/#customize-properties "Permanent link")

In the example above, Spinkit control creates a hardcoded Flutter widget. Now let's customize its properties.

### Common properties[#](https://docs.flet.dev/extend/user-extensions/#common-properties "Permanent link")

Generally, there are three types of controls in Flet:

1. Visual controls that are added to the app/page surface, such as FletSpinkit.
2. Dialog and other popup controls (dialogs, pickers, panels, etc.) that are opened from the page (for example,** **`page.open(dlg)`).
3. Services (Clipboard, Battery, Video, Audio, etc.) that are created as standalone instances and automatically registered with the page.

When creating a visual control that should participate in layout (size, position, transforms, margin, etc.), define a dataclass-based control annotated with** **`@ft.control("control_name")` and inherit from** **[`LayoutControl`](https://docs.flet.dev/controls/layoutcontrol/#flet.LayoutControl). In its Dart counterpart (`src/flet_spinkit.dart`), wrap your Flutter widget with** **`LayoutControl(...)`.

When creating a dialog or other popup control (opened with** **`page.open(...)`), define a dataclass-based control annotated with** **`@ft.control("control_name")` and inherit from** **[`DialogControl`](https://docs.flet.dev/controls/dialogcontrol/#flet.DialogControl). In its Dart counterpart, show the dialog/popup (for example,** **`showDialog` or** **`showModalBottomSheet`) and return a placeholder widget like** **`SizedBox.shrink()` instead of wrapping with** **`LayoutControl(...)` or** **`BaseControl(...)`.

When creating a service control (Clipboard, Battery, Video, Audio, etc.), define a dataclass-based control annotated with** **`@ft.control("control_name")`and inherit from** **[`Service`](https://docs.flet.dev/controls/service/#flet.Service). In its Dart counterpart, implement** **`FletService` and register it via** **`FletExtension.createService` (no widget wrapper).

You can use all** **`LayoutControl`,** **`DialogControl`, and** **`Service` properties inherited by your dataclass-based control without re-declaring them as fields (unless you want to override defaults or metadata).

If you have created your extension project from Flet extension template, your Python Control is already inherited from** **`LayoutControl` and you can use its properties in your example app:

```
importfletasft

fromflet_spinkitimport FletSpinkit


defmain(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(
        ft.Stack(
            [
                ft.Container(height=200, width=200, bgcolor=ft.Colors.BLUE_100),
                FletSpinkit(opacity=0.5, tooltip="Spinkit tooltip", top=0, left=0),
            ]
        )
    )


ft.run(main)
```

[![](https://docs.flet.dev/assets/extensions/spinkit2.gif)](https://docs.flet.dev/assets/extensions/spinkit2.gif)

### Control-specific properties[#](https://docs.flet.dev/extend/user-extensions/#control-specific-properties "Permanent link")

Now that you have taken full advantage of the properties Flet** **`LayoutControl`offer, let's define the properties that are specific to the new Control you are building.

In the FletSpinkit example, let's define its** **`color` and** **`size`.

In Python class, define new** **`color` and** **`size` properties:

```
fromtypingimport Optional

importfletasft


@ft.control("flet_spinkit")
classFletSpinkit(ft.LayoutControl):
"""
    FletSpinkit Control description.
    """

    color: Optional[ft.ColorValue] = None
    size: float = 100.00
```

In** **`src/flet_spinkit.dart` file, use helper methods** **`getColor` and** **`getDouble` to access color and size values:

```
import'package:flet/flet.dart';
import'package:flutter/material.dart';
import'package:flutter_spinkit/flutter_spinkit.dart';

classFletSpinkitControlextendsStatelessWidget{
finalControlcontrol;

constFletSpinkitControl({
super.key,
requiredthis.control,
});

@override
Widgetbuild(BuildContextcontext){
WidgetmyControl=SpinKitRotatingCircle(
color:control.getColor("color",context),
size:control.getDouble("size")??100.0,
);

returnLayoutControl(control:control,child:myControl);
}
}
```

Use** **`color` and** **`size` properties in your app:

```
importfletasft

fromflet_spinkitimport FletSpinkit


defmain(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    page.add(
        ft.Stack(
            controls=[
                ft.Container(height=200, width=200, bgcolor=ft.Colors.BLUE_100),
                FletSpinkit(
                    color=ft.Colors.YELLOW,
                    size=150,
                    opacity=0.5,
                    tooltip="Spinkit tooltip",
                    top=0,
                    left=0,
                ),
            ]
        )
    )


ft.run(main)
```

Rebuild and run:

[![](https://docs.flet.dev/assets/extensions/spinkit3.gif)](https://docs.flet.dev/assets/extensions/spinkit3.gif)

Note

In** **`flet_spinkit.py`, the default values on the Python control exist only to make the class easier to use and discover in Python—they are not automatically passed through to the Dart side. On the Flutter side in** **`flet_spinkit.dart`,** **`size` is a required runtime value, so you must explicitly provide a fallback like** **`control.getDouble("size") ?? 100.0`. Otherwise, if size is not provided, Dart receives null for a required parameter and will throw a runtime error.

You can find source code for this example** **[here](https://github.com/flet-dev/flet-spinkit).

## Examples[#](https://docs.flet.dev/extend/user-extensions/#examples "Permanent link")

Flet has controls that are implemented as** **[built-in extensions](https://docs.flet.dev/extend/built-in-extensions/) and could serve as a starting point for your own controls.
