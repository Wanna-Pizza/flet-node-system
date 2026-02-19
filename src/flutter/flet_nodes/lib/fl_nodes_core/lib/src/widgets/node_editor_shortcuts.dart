import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../core/controller/core.dart';

class FlNodesShortcutsWidget extends StatefulWidget {
  final FlNodesController controller;
  final Widget child;

  const FlNodesShortcutsWidget({
    super.key,
    required this.controller,
    required this.child,
  });

  @override
  State<FlNodesShortcutsWidget> createState() => _FlNodesShortcutsWidgetState();
}

class _FlNodesShortcutsWidgetState extends State<FlNodesShortcutsWidget> {
  // Track pressed physical keys to avoid duplicate handling
  final Set<PhysicalKeyboardKey> _pressed = {};

  @override
  void initState() {
    super.initState();
    RawKeyboard.instance.addListener(_handleRawKey);
  }

  @override
  void dispose() {
    RawKeyboard.instance.removeListener(_handleRawKey);
    super.dispose();
  }

  void _handleRawKey(RawKeyEvent event) {
    // Track primary focus for selective handling below
    final primary = FocusManager.instance.primaryFocus;
    // Only react to key down
    if (event is RawKeyDownEvent) {
      final physical = event.physicalKey;
      if (_pressed.contains(physical)) return; // already handled
      _pressed.add(physical);

      // Shift + D duplication
      if (event.isShiftPressed && event.logicalKey == LogicalKeyboardKey.keyD) {
        // If focus is inside an editable text, ignore duplication to avoid
        // interfering with typing.
        if (primary != null && primary.context != null) {
          final ctx = primary.context!;
          if (ctx.widget is EditableText ||
              ctx.findAncestorWidgetOfExactType<EditableText>() != null) {
            return;
          }
        }
        widget.controller.clipboard.duplicateSelection(
          screenPosition: widget.controller.lastPointerScreenPosition,
          context: context,
        );
      }

      // Ctrl/Cmd + X: cut selection — handle at raw key level so it works even
      // if a field was focused and swallowed the event. We unfocus the text
      // field first so the global cut applies to nodes.
      if ((event.isControlPressed || event.isMetaPressed) &&
          event.logicalKey == LogicalKeyboardKey.keyX) {
        FocusManager.instance.primaryFocus?.unfocus();
        widget.controller.clipboard.cutSelection(context: context);
      }
    } else if (event is RawKeyUpEvent) {
      _pressed.remove(event.physicalKey);
    }
  }

  @override
  Widget build(BuildContext context) {
    final controller = widget.controller;

    return CallbackShortcuts(
      bindings: <ShortcutActivator, VoidCallback>{
        const SingleActivator(LogicalKeyboardKey.delete): () {
          for (final nodeId in controller.selectedNodeIds) {
            controller.removeNodeById(
              nodeId,
              isHandled: nodeId != controller.selectedNodeIds.last,
            );
          }
          for (final link in controller.selectedLinkIds) {
            controller.removeLinkById(link);
          }
          controller.clearSelection();
        },
        const SingleActivator(LogicalKeyboardKey.backspace): () {
          for (final nodeId in controller.selectedNodeIds) {
            controller.removeNodeById(
              nodeId,
              isHandled: nodeId != controller.selectedNodeIds.last,
            );
          }
          for (final link in controller.selectedLinkIds) {
            controller.removeLinkById(link);
          }
          controller.clearSelection();
        },
        const SingleActivator(LogicalKeyboardKey.keyC, control: true): () =>
            controller.clipboard.copySelection(context: context),
        const SingleActivator(LogicalKeyboardKey.keyV, control: true): () =>
            controller.clipboard.pasteSelection(context: context),
        const SingleActivator(LogicalKeyboardKey.keyX, control: true): () =>
            controller.clipboard.cutSelection(context: context),
        const SingleActivator(LogicalKeyboardKey.keyS, control: true): () =>
            controller.project.save(context: context),
        const SingleActivator(LogicalKeyboardKey.keyO, control: true): () =>
            controller.project.load(context: context),
        SingleActivator(
          LogicalKeyboardKey.keyN,
          control: defaultTargetPlatform != TargetPlatform.macOS,
          meta: defaultTargetPlatform == TargetPlatform.macOS,
          shift: true,
        ): () => controller.project.create(context: context),
        const SingleActivator(LogicalKeyboardKey.keyZ, control: true): () =>
            controller.history.undo(),
        const SingleActivator(LogicalKeyboardKey.keyY, control: true): () =>
            controller.history.redo(),
      },
      child: Focus(autofocus: false, child: widget.child),
    );
  }
}
