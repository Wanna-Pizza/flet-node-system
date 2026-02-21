import 'package:flet/flet.dart';
import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_nodes_core/fl_nodes_core.dart';

// Simple type registry populated from Python via `register_type` invoke method.
final Map<String, String> _pythonTypeRegistry = {};

// Lightweight Dart TypeRegistry for mapping type_id -> runtime type info and (de)serializers.
class _TypeRegistryEntry {
  final String typeId;
  final String dartName;
  final dynamic Function(dynamic)? deserializer;

  _TypeRegistryEntry(this.typeId, this.dartName, {this.deserializer});
}

class TypeRegistry {
  final Map<String, _TypeRegistryEntry> _map = {};

  void register(String typeId, String dartName, {dynamic Function(dynamic)? deserializer}) {
    _map[typeId] = _TypeRegistryEntry(typeId, dartName, deserializer: deserializer);
  }

  bool has(String typeId) => _map.containsKey(typeId);

  _TypeRegistryEntry? getEntry(String? typeId) => typeId == null ? null : _map[typeId];

  dynamic deserialize(dynamic payload, String? typeId) {
    if (typeId == null) return payload;
    final e = getEntry(typeId);
    if (e == null) return payload;
    if (e.deserializer != null) return e.deserializer!(payload);
    // default simple conversions for primitives
    switch (e.dartName) {
      case 'double':
        if (payload is num) return payload.toDouble();
        return double.tryParse(payload.toString()) ?? 0.0;
      case 'int':
        if (payload is num) return payload.toInt();
        return int.tryParse(payload.toString()) ?? 0;
      case 'String':
        return payload?.toString();
      case 'bool':
        if (payload is bool) return payload;
        final s = payload?.toString().toLowerCase();
        return s == 'true' || s == '1';
      default:
        return payload;
    }
  }
}

final TypeRegistry _typeRegistry = TypeRegistry()
  ..register('double', 'double')
  ..register('int', 'int')
  ..register('str', 'String')
  ..register('bool', 'bool');

// Registry of active NodesFieldControlState instances by control id.
final Map<String, NodesFieldControlState> _nodesFieldRegistry = {};

NodesFieldControlState? findNodesFieldById(String? id) {
  if (id != null && _nodesFieldRegistry.containsKey(id)) return _nodesFieldRegistry[id];
  return _nodesFieldRegistry.isNotEmpty ? _nodesFieldRegistry.values.first : null;
}

class NodesFieldControl extends StatefulWidget {
  final Control control;

  const NodesFieldControl({
    super.key,
    required this.control,
  });

  @override
  State<NodesFieldControl> createState() => NodesFieldControlState();
}

class NodesFieldControlState extends State<NodesFieldControl>
    with TickerProviderStateMixin {
  late final FlNodesController _controller;

  FlNodesController get controller => _controller;

  late final StreamSubscription _eventSub;
  // cache last selection to avoid flooding Python with identical events
  Set<String>? _lastSelectedIds;

  @override
  void initState() {
    super.initState();
    debugPrint("FletNodesControl.initState");

    _controller = FlNodesController(appVersion: '0.0.1');
    _controller.setTickerProvider(this);

    // listen for Python invoke-method calls (e.g. add_node)
    widget.control.addInvokeMethodListener(_invokeMethod);

    // listen for selection changes and link events via the controller event bus
    _eventSub = _controller.eventBus.events.listen((event) {
      try {
        if (event is FlNodeSelectionEvent) {
          final selected = event.nodeIds;
          final selectedSet = selected.toSet();
          // if selection hasn't changed, skip emitting
          if (_lastSelectedIds != null && _lastSelectedIds!.length == selectedSet.length && _lastSelectedIds!.containsAll(selectedSet)) {
            return;
          }
          _lastSelectedIds = selectedSet;

          if (selected.isEmpty) {
            widget.control.triggerEvent('node_selected', {'id': null});
          } else if (selected.length == 1) {
            final id = selected.first;
            widget.control.triggerEvent('node_selected', {'id': id});
          } else {
            widget.control.triggerEvent('node_selected', {'ids': selected.toList()});
          }
        } else if (event is FlAddLinkEvent) {
          // emit link_created event to Python
          final link = event.link;
          final fromPort = link.ports.$1;  // First port (source)
          final toPort = link.ports.$2;    // Second port (destination)
          
          widget.control.triggerEvent('link_created', {
            'from_node': fromPort.nodeId,
            'from_port': fromPort.portId,
            'to_node': toPort.nodeId,
            'to_port': toPort.portId,
            'link_id': link.id,
          });
          debugPrint('NodesField: link_created ${fromPort.nodeId}.${fromPort.portId} -> ${toPort.nodeId}.${toPort.portId}');
        } else if (event is FlRemoveLinkEvent) {
          // emit link_removed event to Python
          final link = event.link;
          final fromPort = link.ports.$1;  // First port (source)
          final toPort = link.ports.$2;    // Second port (destination)
          
          widget.control.triggerEvent('link_removed', {
            'from_node': fromPort.nodeId,
            'from_port': fromPort.portId,
            'to_node': toPort.nodeId,
            'to_port': toPort.portId,
            'link_id': link.id,
          });
          debugPrint('NodesField: link_removed ${fromPort.nodeId}.${fromPort.portId} -> ${toPort.nodeId}.${toPort.portId}');
        }
      } catch (e) {
        debugPrint('NodesField.eventBus listener error: $e');
      }
    });

    debugPrint("FletNodes: registering node prototype 'simple.value'");
    _controller.registerNodePrototype(
      FlNodePrototype(
        idName: 'simple.value',
        displayName: (ctx) => 'Value',
        description: (ctx) => 'A simple value node',
        fieldPrototypes: [
          FlFieldPrototype(
            idName: 'value',
            displayName: (ctx) => 'Value',
            dataType: String,
            defaultData: '',
            visualizerBuilder: (data) => Text(
              data?.toString() ?? '',
              style: const TextStyle(color: Colors.white),
              maxLines: 1,
              overflow: TextOverflow.ellipsis,
            ),
          )
        ],
      ),
    );
  }

  @override
  void dispose() {
    widget.control.removeInvokeMethodListener(_invokeMethod);
    _eventSub.cancel();
    _controller.dispose();
    super.dispose();
  }

  Widget _nodeBuilder(FlNodeDataModel node, FlNodesController controller) {
    debugPrint("FletNodes: building node widget for ${node.id}");
    return FlDefaultNodeWidget(
      controller: controller,
      node: node,
      showPortContextMenu: (ctx, pos, ctrl, locator) {
        debugPrint("showPortContextMenu: node=${node.id}");
      },
      showNodeCreationMenu: (ctx, lastFocalPoint, ctrl, locator, onTmp) {
        debugPrint("showNodeCreationMenu");
      },
      showNodeContextMenu: (ctx, pos, ctrl, node) {
        debugPrint("showNodeContextMenu: node=${node.id}");
      },
    );
  }

  void _showPortContextMenu(BuildContext context, Offset position,
      FlNodesController controller, PortLocator locator) {}

  void _showCanvasContextMenu(BuildContext context, Offset position,
      FlNodesController controller, PortLocator? locator) {}

  void _showNodeCreationMenu(BuildContext context, Offset lastFocalPoint,
      FlNodesController controller, PortLocator? locator, void Function() onTmp) {}

  void _showLinkContextMenu(BuildContext context, String linkId, Offset pos,
      FlNodesController controller) {}

  Future<dynamic> _invokeMethod(String name, dynamic args) async {
    debugPrint('NodesField._invokeMethod: $name $args');
    switch (name) {
      case 'register_type':
        return await _handleRegisterType(args);
      case 'add_node':
        return await _handleAddNode(args);
      case 'remove_node':
        return await _handleRemoveNode(args);
      case 'clear_nodes':
        return await _handleClearNodes(args);
      case 'add_link':
        return await _handleAddLink(args);
      default:
        throw Exception('Unknown NodesField method: $name');
    }
  }

  Future<dynamic> _handleRegisterType(dynamic args) async {
    try {
      final typeId = args['type_id'] as String?;
      final dartType = args['dart_type'] as String?;
      if (typeId != null) {
        _pythonTypeRegistry[typeId] = dartType ?? 'dynamic';
        if (dartType != null) {
          _typeRegistry.register(typeId, dartType);
        } else {
          _typeRegistry.register(typeId, 'dynamic');
        }
        debugPrint('NodesField: registered type $typeId -> ${_pythonTypeRegistry[typeId]}');
        return true;
      }
    } catch (e) {
      debugPrint('NodesField: register_type failed: $e');
    }
    return false;
  }

  Future<dynamic> _handleAddNode(dynamic args) async {
    final prototype = (args["prototype"] as String?) ?? 'simple.value';
    final double x = (args["x"] is num) ? (args["x"] as num).toDouble() : 0.0;
    final double y = (args["y"] is num) ? (args["y"] as num).toDouble() : 0.0;
    List<dynamic>? inputs = args['inputs'] as List<dynamic>?;
    List<dynamic>? outputs = args['outputs'] as List<dynamic>?;

    String prototypeId = prototype;
    if ((inputs != null && inputs.isNotEmpty) || (outputs != null && outputs.isNotEmpty)) {
      final List<FlPortPrototype> portPrototypes = [];

      inputs?.forEach((spec) {
        try {
          final id = spec is Map ? (spec['id'] ?? spec['idName']) : spec.toString();
          final label = (spec is Map && spec['displayName'] != null) ? spec['displayName'].toString() : id.toString();
          final typeLabel = (spec is Map && spec['type'] != null) ? spec['type'].toString() : null;

          // Special-case control/execution ports
          if (typeLabel == 'exec' || typeLabel == 'execution') {
            portPrototypes.add(FlControlInputPortPrototype(
              idName: id.toString(),
              displayName: (ctx) => label,
              geometricOrientation: FlPortGeometricOrientation.left,
              styleBuilder: flDefaultPortStyleBuilder,
            ));
            return;
          }

          if (typeLabel != null && _typeRegistry.has(typeLabel)) {
            final entry = _typeRegistry.getEntry(typeLabel)!;
            switch (entry.dartName) {
              case 'double':
                portPrototypes.add(FlDataInputPortPrototype<double>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  geometricOrientation: FlPortGeometricOrientation.left,
                ));
                break;
              case 'int':
                portPrototypes.add(FlDataInputPortPrototype<int>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  geometricOrientation: FlPortGeometricOrientation.left,
                ));
                break;
              case 'String':
                portPrototypes.add(FlDataInputPortPrototype<String>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  geometricOrientation: FlPortGeometricOrientation.left,
                ));
                break;
              case 'bool':
                portPrototypes.add(FlDataInputPortPrototype<bool>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  geometricOrientation: FlPortGeometricOrientation.left,
                ));
                break;
              default:
                portPrototypes.add(FlDataInputPortPrototype<dynamic>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  geometricOrientation: FlPortGeometricOrientation.left,
                ));
            }
          } else {
            portPrototypes.add(FlDataInputPortPrototype<dynamic>(
              idName: id.toString(),
              displayName: (ctx) => label,
              geometricOrientation: FlPortGeometricOrientation.left,
            ));
          }
        } catch (e) {
          debugPrint('NodesField: failed to build input port prototype: $e');
        }
      });

      outputs?.forEach((spec) {
        try {
          final id = spec is Map ? (spec['id'] ?? spec['idName']) : spec.toString();
          final label = (spec is Map && spec['displayName'] != null) ? spec['displayName'].toString() : id.toString();
          final typeLabel = (spec is Map && spec['type'] != null) ? spec['type'].toString() : null;
          final link = FlLinkPrototype(label: (_) => typeLabel ?? '');

          // Control / exec output ports
          if (typeLabel == 'exec' || typeLabel == 'execution') {
            portPrototypes.add(FlControlOutputPortPrototype(
              idName: id.toString(),
              displayName: (ctx) => label,
              geometricOrientation: FlPortGeometricOrientation.right,
              styleBuilder: flDefaultPortStyleBuilder,
            ));
            return;
          }

          if (typeLabel != null && _typeRegistry.has(typeLabel)) {
            final entry = _typeRegistry.getEntry(typeLabel)!;
            switch (entry.dartName) {
              case 'double':
                portPrototypes.add(FlDataOutputPortPrototype<double>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  linkPrototype: link,
                  geometricOrientation: FlPortGeometricOrientation.right,
                ));
                break;
              case 'int':
                portPrototypes.add(FlDataOutputPortPrototype<int>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  linkPrototype: link,
                  geometricOrientation: FlPortGeometricOrientation.right,
                ));
                break;
              case 'String':
                portPrototypes.add(FlDataOutputPortPrototype<String>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  linkPrototype: link,
                  geometricOrientation: FlPortGeometricOrientation.right,
                ));
                break;
              case 'bool':
                portPrototypes.add(FlDataOutputPortPrototype<bool>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  linkPrototype: link,
                  geometricOrientation: FlPortGeometricOrientation.right,
                ));
                break;
              default:
                portPrototypes.add(FlDataOutputPortPrototype<dynamic>(
                  idName: id.toString(),
                  displayName: (ctx) => label,
                  linkPrototype: link,
                  geometricOrientation: FlPortGeometricOrientation.right,
                ));
            }
          } else {
            portPrototypes.add(FlDataOutputPortPrototype<dynamic>(
              idName: id.toString(),
              displayName: (ctx) => label,
              linkPrototype: link,
              geometricOrientation: FlPortGeometricOrientation.right,
            ));
          }
        } catch (e) {
          debugPrint('NodesField: failed to build output port prototype: $e');
        }
      });

      final specString = '${prototype}|${inputs?.toString() ?? ''}|${outputs?.toString() ?? ''}';
      final safe = specString.replaceAll(RegExp(r"[^A-Za-z0-9_\.\-]"), '_');
      prototypeId = '${prototype}.pytemp.$safe';
      final tempPrototype = FlNodePrototype(
        idName: prototypeId,
        displayName: (ctx) => prototype,
        description: (ctx) => '',
        portPrototypes: portPrototypes,
        fieldPrototypes: [],
      );
      try {
        _controller.registerNodePrototype(tempPrototype);
      } catch (e) {
        debugPrint('NodesField: failed to register temp prototype: $e');
      }
    }

    final node = _controller.addNode(prototypeId, offset: Offset(x, y));

    try {
      final created = _controller.nodes[node.id];
      if (created != null) {
        void applyDefaults(List<dynamic>? specs) {
          specs?.forEach((spec) {
            if (spec is Map) {
              final pid = spec['id'] ?? spec['idName'];
              final typeLabel = spec['type'] as String?;
              if (pid != null && created.ports.containsKey(pid)) {
                try {
                  final def = spec['default'];
                  if (def != null) {
                    final value = _typeRegistry.deserialize(def, typeLabel);
                    created.ports[pid]!.data = value;
                  }
                } catch (e) {
                  debugPrint('NodesField: failed to set default for port $pid: $e');
                }
              }
            }
          });
        }

        applyDefaults(inputs);
        applyDefaults(outputs);
      }
    } catch (e) {
      debugPrint('NodesField: error applying defaults: $e');
    }

    return {'id': node.id, 'x': x, 'y': y};
  }

  Future<dynamic> _handleRemoveNode(dynamic args) async {
    final id = args['id'] as String?;
    if (id != null) {
      _controller.removeNodeById(id);
      return true;
    }
    return false;
  }

  Future<dynamic> _handleClearNodes(dynamic args) async {
    final ids = _controller.nodes.keys.toList();
    for (final id in ids) {
      debugPrint('NodesField._invokeMethod: removing node $id');
      _controller.removeNodeById(id);
    }
    return true;
  }

  // Programmatic link creation from Python
  Future<dynamic> _handleAddLink(dynamic args) async {
    try {
      final fromNode = args['from_node'] as String?;
      final fromPort = args['from_port'] as String?;
      final toNode = args['to_node'] as String?;
      final toPort = args['to_port'] as String?;

      if (fromNode == null || fromPort == null || toNode == null || toPort == null) {
        debugPrint('NodesField: add_link failed - missing args: $args');
        return {'error': 'missing_args', 'args': args};
      }

      // Validate nodes and ports exist to give better diagnostics
      if (!controller.nodes.containsKey(fromNode)) {
        debugPrint('NodesField: add_link failed - source node not found: $fromNode');
        return {'error': 'source_node_not_found', 'node': fromNode};
      }
      if (!controller.nodes.containsKey(toNode)) {
        debugPrint('NodesField: add_link failed - target node not found: $toNode');
        return {'error': 'target_node_not_found', 'node': toNode};
      }

      final fromNodeModel = controller.nodes[fromNode]!;
      final toNodeModel = controller.nodes[toNode]!;

      if (!fromNodeModel.ports.containsKey(fromPort)) {
        debugPrint('NodesField: add_link failed - source port not found: $fromPort on $fromNode');
        return {'error': 'source_port_not_found', 'node': fromNode, 'port': fromPort};
      }
      if (!toNodeModel.ports.containsKey(toPort)) {
        debugPrint('NodesField: add_link failed - target port not found: $toPort on $toNode');
        return {'error': 'target_port_not_found', 'node': toNode, 'port': toPort};
      }

      // Attempt to add link
      final link = controller.addLink(fromNode, fromPort, toNode, toPort);
      if (link != null) {
        return {'id': link.id};
      }

      debugPrint('NodesField: add_link - controller rejected link: $fromNode.$fromPort -> $toNode.$toPort');
      return {'error': 'rejected_by_controller'};
    } catch (e) {
      debugPrint('NodesField: add_link failed: $e');
      return {'error': 'exception', 'message': e.toString()};
    }
  }

  @override
  Widget build(BuildContext context) {
    debugPrint("NodesField.build: control=${widget.control.type}");

    final flNodes = FlNodesShortcutsWidget(
      controller: _controller,
      child: FlNodesWidget(
        controller: _controller,
        nodeBuilder: (node, controller) => _nodeBuilder(node, controller),
        showPortContextMenu: _showPortContextMenu,
        showCanvasContextMenu: _showCanvasContextMenu,
        showNodeCreationMenu: _showNodeCreationMenu,
        showLinkContextMenu: _showLinkContextMenu,
      ),
    );

    return LayoutControl(
      control: widget.control,
      child: SizedBox.expand(child: flNodes),
    );
  }
}
