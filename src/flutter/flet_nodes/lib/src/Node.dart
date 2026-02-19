import 'package:flet/flet.dart';
import 'package:flutter/material.dart';
import 'package:fl_nodes_core/fl_nodes_core.dart';
import 'NodesField.dart';

class NodeControl extends StatefulWidget {
  final Control control;

  const NodeControl({
    super.key,
    required this.control,
  });

  @override
  State<NodeControl> createState() => _NodeControlState();
}

class _NodeControlState extends State<NodeControl>
    with TickerProviderStateMixin {
  late FlNodesController _controller;
  String? _createdNodeId;
  bool _registered = false;

  @override
  void initState() {
    super.initState();
    debugPrint("NodeControl.initState");
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();

    if (_registered) return;

    // Try to find target field by explicit `fieldId` or take the first available field
    final String? fieldId = widget.control.getString('fieldId');
    final parentState = findNodesFieldById(fieldId);

    if (parentState != null) {
      _controller = parentState.controller;

      final double x = widget.control.getDouble("x") ?? 0.0;
      final double y = widget.control.getDouble("y") ?? 0.0;

      final node = _controller.addNode('simple.value', offset: Offset(x, y));
      _createdNodeId = node.id;
      debugPrint('NodeControl: registered node ${_createdNodeId} -> field=${parentState.widget.control.id}');
      _registered = true;
      return;
    }

    // If field not found yet (different order in tree), try again next frame
    WidgetsBinding.instance.addPostFrameCallback((_) => _tryRegister());
  }

  @override
  void dispose() {
    if (_createdNodeId != null) {
      try {
        _controller.removeNodeById(_createdNodeId!);
      } catch (_) {}
    }
    super.dispose();
  }

  void _tryRegister() {
    if (_registered) return;
    final String? fieldId = widget.control.getString('fieldId');
    final parentState = findNodesFieldById(fieldId);
    if (parentState == null) {
      debugPrint('NodeControl._tryRegister: field not found (fieldId=$fieldId)');
      return;
    }

    _controller = parentState.controller;
    final double x = widget.control.getDouble("x") ?? 0.0;
    final double y = widget.control.getDouble("y") ?? 0.0;

    final node = _controller.addNode('simple.value', offset: Offset(x, y));
    _createdNodeId = node.id;
    debugPrint('NodeControl._tryRegister: registered node ${_createdNodeId} -> field=${parentState.widget.control.id}');
    _registered = true;
  }

  @override
  Widget build(BuildContext context) {
    // Node itself does not render UI; it's managed by the parent NodesField's FlNodes canvas.
    return LayoutControl(control: widget.control, child: const SizedBox.shrink());
  }
}
