import 'package:flet/flet.dart';
import 'package:flutter/widgets.dart';

import 'Node.dart';
import 'NodesField.dart';

class Extension extends FletExtension {
  @override
  Widget? createWidget(Key? key, Control control) {
    switch (control.type) {
      case "NodesField":
        return NodesFieldControl(control: control);
      case "Node":
        return NodeControl(control: control);
      default:
        return null;
    }
  }
}
