"""HTML+JS template for the React Flow viewer.

Loaded once and string-formatted with the payload + dimensions. No JSX — we
use React.createElement directly so the page renders without a transpile step.
"""

# {payload_json} is the only safe substitution; height/width are numbers.
# Anything else inside the template uses {{ }} to escape literal braces.
TEMPLATE = r"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  html, body, #root {{ width: 100%; height: 100%; background: #fafbfc; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif; color: #1a1f29; }}
  .sticky {{
    min-width: 150px; max-width: 220px;
    padding: 8px 10px;
    border-radius: 6px;
    border: 1.5px solid;
    font-size: 11px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.08);
    position: relative;
  }}
  .sticky .subtitle {{
    font-size: 8px;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: 3px;
  }}
  .sticky .label {{
    font-weight: 600;
    line-height: 1.25;
    margin-bottom: 4px;
    word-break: break-word;
  }}
  .sticky .id {{
    font-family: 'SF Mono', Menlo, Consolas, monospace;
    font-size: 8.5px;
    opacity: 0.55;
    word-break: break-all;
  }}
  .sticky .state-badge {{
    position: absolute; top: 4px; right: 6px;
    font-size: 7.5px; padding: 1px 5px; border-radius: 2px;
    text-transform: uppercase; letter-spacing: 0.1em; font-weight: 700;
  }}
  .state-nuevo      {{ background: #c8e6c9; color: #1b5e20; }}
  .state-modificado {{ background: #fff3e0; color: #e65100; }}
  .state-eliminado  {{ background: #ffcdd2; color: #b71c1c; }}

  .legend {{
    position: absolute; bottom: 60px; left: 16px; z-index: 5;
    background: rgba(255,255,255,0.95); padding: 8px 10px;
    border: 0.6pt solid #d2dae6; border-radius: 6px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    font-size: 10px;
  }}
  .legend .row {{ display: flex; align-items: center; gap: 6px; margin: 2px 0; }}
  .legend .swatch {{ width: 12px; height: 10px; border-radius: 2px; border: 1px solid rgba(0,0,0,0.18); }}

  .sticky {{ cursor: grab; }}
  .sticky:active {{ cursor: grabbing; }}

  .node-tooltip {{
    position: absolute; bottom: 100%; left: 0; margin-bottom: 8px;
    width: 240px; z-index: 1000;
    background: #0a2540; color: #fff;
    padding: 8px 10px; border-radius: 6px;
    font-size: 10px; line-height: 1.4;
    box-shadow: 0 4px 14px rgba(0,0,0,0.28);
    pointer-events: none; white-space: normal; text-align: left;
  }}
  .node-tooltip::after {{
    content: ''; position: absolute; top: 100%; left: 16px;
    border: 5px solid transparent; border-top-color: #0a2540;
  }}
  .node-tooltip .tt-type {{
    text-transform: uppercase; letter-spacing: 0.08em;
    opacity: 0.65; font-size: 8px; margin-bottom: 2px;
  }}
  .node-tooltip .tt-name {{ font-weight: 700; margin-bottom: 4px; font-size: 11px; }}
  .node-tooltip .tt-desc {{ opacity: 0.92; }}
  .node-tooltip .tt-id {{
    font-family: 'SF Mono', Menlo, Consolas, monospace;
    font-size: 8px; opacity: 0.55; margin-top: 5px; word-break: break-all;
  }}
  .node-tooltip .tt-tags {{ margin-top: 6px; display: flex; flex-wrap: wrap; gap: 3px; }}
  .node-tooltip .tt-tag {{
    background: rgba(255,255,255,0.16); padding: 1px 5px;
    border-radius: 3px; font-size: 8px;
  }}
</style>
<link rel="stylesheet" href="https://esm.sh/reactflow@11.11.4/dist/style.css" />
</head>
<body>
<div id="root"></div>

<script type="module">
import React from 'https://esm.sh/react@18.3.1';
import {{ createRoot }} from 'https://esm.sh/react-dom@18.3.1/client';
import RF, {{
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Handle,
  Position,
  useNodesState,
  useEdgesState,
}} from 'https://esm.sh/reactflow@11.11.4?deps=react@18.3.1,react-dom@18.3.1';
import dagre from 'https://esm.sh/dagre@0.8.5';

const PAYLOAD = {payload_json};

const TYPE_STYLES = {{
  actor:           {{ bg: '#FFF9C4', fg: '#5D4037', border: '#F9A825' }},
  sistema_externo: {{ bg: '#ECEFF1', fg: '#37474F', border: '#78909C' }},
  comando:         {{ bg: '#BBDEFB', fg: '#0D47A1', border: '#42A5F5' }},
  agregado:        {{ bg: '#FFF3E0', fg: '#E65100', border: '#FB8C00' }},
  entidad_raiz:    {{ bg: '#FFF3E0', fg: '#E65100', border: '#FB8C00' }},
  evento:          {{ bg: '#FFE0B2', fg: '#BF360C', border: '#FB8C00' }},
  politica:        {{ bg: '#E8EAF6', fg: '#283593', border: '#7C4DFF' }},
  politica_ui:     {{ bg: '#F3E5F5', fg: '#6A1B9A', border: '#AB47BC' }},
  regla:           {{ bg: '#EDE7F6', fg: '#4A148C', border: '#9C27B0' }},
  read_model:      {{ bg: '#E8F5E9', fg: '#1B5E20', border: '#43A047' }},
  vista:           {{ bg: '#E8F5E9', fg: '#1B5E20', border: '#43A047' }},
  proyeccion:      {{ bg: '#E8F5E9', fg: '#1B5E20', border: '#43A047' }},
  hotspot:         {{ bg: '#FFEBEE', fg: '#B71C1C', border: '#EF5350' }},
  default:         {{ bg: '#F5F5F5', fg: '#333',   border: '#BDBDBD' }},
}};

function StickyNode(props) {{
  const t = TYPE_STYLES[props.type] || TYPE_STYLES.default;
  const data = props.data || {{}};
  const state = data.state || 'existente';
  const tags = data.tags || [];
  const [hover, setHover] = React.useState(false);
  const badge = state !== 'existente'
    ? React.createElement('span', {{
        className: 'state-badge state-' + state,
      }}, state)
    : null;

  const tooltip = hover
    ? React.createElement(
        'div',
        {{ className: 'node-tooltip' }},
        React.createElement('div', {{ className: 'tt-type' }}, data.subtitle || ''),
        React.createElement('div', {{ className: 'tt-name' }}, data.label || ''),
        data.description
          ? React.createElement('div', {{ className: 'tt-desc' }}, data.description)
          : React.createElement('div', {{ className: 'tt-desc', style: {{ opacity: 0.5 }} }}, 'Sin descripción.'),
        tags.length
          ? React.createElement(
              'div',
              {{ className: 'tt-tags' }},
              tags.map(function (tag, i) {{
                return React.createElement('span', {{ className: 'tt-tag', key: i }}, tag);
              }})
            )
          : null,
        React.createElement('div', {{ className: 'tt-id' }}, data.id || ''),
      )
    : null;

  return React.createElement(
    'div',
    {{
      className: 'sticky',
      style: {{
        background: t.bg, color: t.fg, borderColor: t.border,
      }},
      onMouseEnter: function () {{ setHover(true); }},
      onMouseLeave: function () {{ setHover(false); }},
    }},
    React.createElement(Handle, {{ type: 'target', position: Position.Left, style: {{ background: t.border }} }}),
    badge,
    tooltip,
    React.createElement('div', {{ className: 'subtitle' }}, data.subtitle || ''),
    React.createElement('div', {{ className: 'label' }}, data.label),
    React.createElement('div', {{ className: 'id' }}, data.id),
    React.createElement(Handle, {{ type: 'source', position: Position.Right, style: {{ background: t.border }} }}),
  );
}}

const nodeTypes = {{
  actor: StickyNode,
  sistema_externo: StickyNode,
  comando: StickyNode,
  agregado: StickyNode,
  entidad_raiz: StickyNode,
  evento: StickyNode,
  politica: StickyNode,
  politica_ui: StickyNode,
  regla: StickyNode,
  read_model: StickyNode,
  vista: StickyNode,
  proyeccion: StickyNode,
  hotspot: StickyNode,
}};

function layoutWithDagre(nodes, edges, direction) {{
  const g = new dagre.graphlib.Graph();
  g.setGraph({{ rankdir: direction || 'LR', nodesep: 35, ranksep: 60, marginx: 20, marginy: 20 }});
  g.setDefaultEdgeLabel(function () {{ return {{}}; }});
  const W = 200, H = 90;
  nodes.forEach(function (n) {{ g.setNode(n.id, {{ width: W, height: H }}); }});
  edges.forEach(function (e) {{ g.setEdge(e.source, e.target); }});
  dagre.layout(g);
  return nodes.map(function (n) {{
    const p = g.node(n.id);
    return Object.assign({{}}, n, {{
      position: {{ x: p.x - W / 2, y: p.y - H / 2 }},
      sourcePosition: (direction === 'TB') ? Position.Bottom : Position.Right,
      targetPosition: (direction === 'TB') ? Position.Top : Position.Left,
    }});
  }});
}}

// Build an ordered list of walkthrough steps: a DFS from each actor (or, if
// there are none, from indegree-0 roots) that grows a flow-tree. Each step
// snapshots the nodes/edges visited so far for the current root, so advancing
// reveals the tree branch by branch; a final sweep covers unreachable nodes.
function buildTourSteps(nodes, edges) {{
  const adj = {{}};
  edges.forEach(function (e) {{ (adj[e.source] = adj[e.source] || []).push(e); }});
  const indeg = {{}};
  nodes.forEach(function (n) {{ indeg[n.id] = 0; }});
  edges.forEach(function (e) {{ if (indeg[e.target] != null) indeg[e.target] += 1; }});

  const actors = nodes.filter(function (n) {{ return n.type === 'actor'; }}).map(function (n) {{ return n.id; }});
  const roots = actors.length
    ? actors.slice()
    : nodes.filter(function (n) {{ return (indeg[n.id] || 0) === 0; }}).map(function (n) {{ return n.id; }});

  const steps = [];
  const covered = new Set();

  function traverse(rootId) {{
    const visN = new Set();
    const visE = new Set();
    const seen = new Set();
    function dfs(nodeId, viaEdge) {{
      visN.add(nodeId);
      if (viaEdge) visE.add(viaEdge.id);
      covered.add(nodeId);
      steps.push({{
        actorId: rootId,
        focusNode: nodeId,
        focusEdge: viaEdge ? viaEdge.id : null,
        parentNode: viaEdge ? viaEdge.source : null,
        visibleNodes: new Set(visN),
        visibleEdges: new Set(visE),
      }});
      if (seen.has(nodeId)) return;
      seen.add(nodeId);
      (adj[nodeId] || []).forEach(function (e) {{
        if (!seen.has(e.target)) dfs(e.target, e);
      }});
    }}
    dfs(rootId, null);
  }}

  roots.forEach(function (r) {{ traverse(r); }});
  nodes.forEach(function (n) {{ if (!covered.has(n.id)) traverse(n.id); }});
  return steps;
}}

function App() {{
  const [direction, setDirection] = React.useState('LR');
  const styledEdges = React.useMemo(function () {{
    return PAYLOAD.edges.map(function (e) {{
      return Object.assign({{}}, e, {{
        type: 'smoothstep',
        animated: false,
        style: {{ stroke: '#94a3b8', strokeWidth: 1.4 }},
        labelStyle: {{ fontSize: 10, fill: '#475569' }},
        labelBgStyle: {{ fill: 'rgba(255,255,255,0.9)' }},
        labelBgPadding: [4, 2],
        markerEnd: {{ type: 'arrowclosed', color: '#94a3b8' }},
      }});
    }});
  }}, []);

  // Controlled state so dragging a node persists; edges re-route to follow it.
  const [nodes, setNodes, onNodesChange] = useNodesState(
    layoutWithDagre(PAYLOAD.nodes, styledEdges, 'LR')
  );
  const [edges, setEdges, onEdgesChange] = useEdgesState(styledEdges);

  // Re-run the dagre layout whenever the flow direction toggles.
  React.useEffect(function () {{
    setNodes(layoutWithDagre(PAYLOAD.nodes, styledEdges, direction));
  }}, [direction]);

  // Clicking an edge focuses it: the edge + its two endpoints stay solid, the
  // rest of the graph dims so you can follow the direction at a glance.
  const [focusEdge, setFocusEdge] = React.useState(null);

  // ── Guided walkthrough (assistant) ──────────────────────────────────────
  const nodeById = React.useMemo(function () {{
    const m = {{}};
    PAYLOAD.nodes.forEach(function (n) {{ m[n.id] = n; }});
    return m;
  }}, []);
  const steps = React.useMemo(function () {{ return buildTourSteps(PAYLOAD.nodes, PAYLOAD.edges); }}, []);
  const [tour, setTour] = React.useState(false);
  const [stepIdx, setStepIdx] = React.useState(0);
  const rfInstance = React.useRef(null);
  const tourStep = (tour && steps.length) ? steps[Math.min(stepIdx, steps.length - 1)] : null;

  function startTour() {{ setFocusEdge(null); setStepIdx(0); setTour(true); }}
  function exitTour() {{
    setTour(false);
    if (rfInstance.current) rfInstance.current.fitView({{ padding: 0.2, duration: 400 }});
  }}
  function nextStep() {{ setStepIdx(function (i) {{ return Math.min(i + 1, steps.length - 1); }}); }}
  function prevStep() {{ setStepIdx(function (i) {{ return Math.max(i - 1, 0); }}); }}

  // Pan/zoom to the current step (focus node + its parent for context).
  React.useEffect(function () {{
    if (!tourStep || !rfInstance.current) return;
    const ids = tourStep.parentNode
      ? [{{ id: tourStep.parentNode }}, {{ id: tourStep.focusNode }}]
      : [{{ id: tourStep.focusNode }}];
    rfInstance.current.fitView({{ nodes: ids, duration: 450, padding: 0.5, maxZoom: 1.4 }});
  }}, [tourStep]);

  const displayNodes = React.useMemo(function () {{
    if (tourStep) {{
      return nodes.map(function (n) {{
        const visible = tourStep.visibleNodes.has(n.id);
        const isFocus = n.id === tourStep.focusNode;
        return Object.assign({{}}, n, {{
          style: Object.assign({{}}, n.style, {{
            opacity: visible ? (isFocus ? 1 : 0.5) : 0.04,
            transition: 'opacity 0.25s',
          }}),
        }});
      }});
    }}
    if (!focusEdge) {{
      return nodes.map(function (n) {{
        return Object.assign({{}}, n, {{ style: Object.assign({{}}, n.style, {{ opacity: 1, transition: 'opacity 0.2s' }}) }});
      }});
    }}
    const fe = edges.find(function (x) {{ return x.id === focusEdge; }});
    const keep = fe ? new Set([fe.source, fe.target]) : new Set();
    return nodes.map(function (n) {{
      const on = keep.has(n.id);
      return Object.assign({{}}, n, {{
        style: Object.assign({{}}, n.style, {{ opacity: on ? 1 : 0.12, transition: 'opacity 0.2s' }}),
      }});
    }});
  }}, [nodes, edges, focusEdge, tourStep]);

  const displayEdges = React.useMemo(function () {{
    return edges.map(function (ed) {{
      if (tourStep) {{
        const visible = tourStep.visibleEdges.has(ed.id);
        const isFocus = ed.id === tourStep.focusEdge;
        const stroke = isFocus ? '#0a2540' : '#94a3b8';
        return Object.assign({{}}, ed, {{
          animated: !!isFocus,
          style: Object.assign({{}}, ed.style, {{
            stroke: stroke,
            strokeWidth: isFocus ? 2.8 : 1.4,
            opacity: visible ? (isFocus ? 1 : 0.45) : 0.03,
            transition: 'opacity 0.25s',
          }}),
          labelStyle: Object.assign({{}}, ed.labelStyle, {{ opacity: visible ? 1 : 0.03 }}),
          labelBgStyle: Object.assign({{}}, ed.labelBgStyle, {{ opacity: visible ? 1 : 0.03 }}),
          markerEnd: {{ type: 'arrowclosed', color: stroke }},
        }});
      }}
      const sel = focusEdge && ed.id === focusEdge;
      const on = !focusEdge || sel;
      const stroke = sel ? '#0a2540' : '#94a3b8';
      return Object.assign({{}}, ed, {{
        animated: !!sel,
        style: Object.assign({{}}, ed.style, {{
          stroke: stroke,
          strokeWidth: sel ? 2.6 : 1.4,
          opacity: on ? 1 : 0.07,
          transition: 'opacity 0.2s',
        }}),
        labelStyle: Object.assign({{}}, ed.labelStyle, {{ opacity: on ? 1 : 0.07 }}),
        labelBgStyle: Object.assign({{}}, ed.labelBgStyle, {{ opacity: on ? 1 : 0.07 }}),
        markerEnd: {{ type: 'arrowclosed', color: stroke }},
      }});
    }});
  }}, [edges, focusEdge, tourStep]);

  const toolbar = React.createElement(
    'div',
    {{
      style: {{
        position: 'absolute', top: 10, right: 10, zIndex: 5,
        background: '#fff', border: '1px solid #d2dae6', borderRadius: 6,
        padding: '4px 6px', fontSize: 11,
      }},
    }},
    React.createElement('span', {{ style: {{ marginRight: 8, color: '#475569' }} }}, 'Flujo:'),
    React.createElement('button', {{
      onClick: function () {{ setDirection('LR'); }},
      title: 'Las flechas avanzan hacia la derecha',
      style: {{
        marginRight: 4, padding: '3px 10px',
        background: direction === 'LR' ? '#0a2540' : '#fff',
        color: direction === 'LR' ? '#fff' : '#0a2540',
        border: '1px solid #0a2540', borderRadius: 4, cursor: 'pointer',
        fontFamily: 'inherit',
      }},
    }}, '→ horizontal'),
    React.createElement('button', {{
      onClick: function () {{ setDirection('TB'); }},
      title: 'Las flechas avanzan hacia abajo',
      style: {{
        padding: '3px 10px',
        background: direction === 'TB' ? '#0a2540' : '#fff',
        color: direction === 'TB' ? '#fff' : '#0a2540',
        border: '1px solid #0a2540', borderRadius: 4, cursor: 'pointer',
        fontFamily: 'inherit',
      }},
    }}, '↓ vertical'),
    React.createElement('button', {{
      onClick: startTour,
      disabled: !steps.length,
      title: 'Recorrido guiado del flujo, paso a paso desde cada actor',
      style: {{
        marginLeft: 10, padding: '3px 10px',
        background: tour ? '#0a2540' : '#fff',
        color: tour ? '#fff' : '#0a2540',
        border: '1px solid #0a2540', borderRadius: 4,
        cursor: steps.length ? 'pointer' : 'not-allowed',
        opacity: steps.length ? 1 : 0.4, fontFamily: 'inherit',
      }},
    }}, '▶ Asistente'),
  );

  // Step-by-step assistant panel (only while the walkthrough is active).
  const focusData = tourStep ? ((nodeById[tourStep.focusNode] || {{}}).data || {{}}) : {{}};
  let connText = 'Inicio del flujo';
  if (tourStep && tourStep.focusEdge) {{
    const fe = PAYLOAD.edges.find(function (x) {{ return x.id === tourStep.focusEdge; }});
    const parent = nodeById[tourStep.parentNode];
    const parentName = parent ? (parent.data.label || tourStep.parentNode) : tourStep.parentNode;
    const rel = fe && fe.label ? fe.label : 'conecta';
    connText = parentName + '  —[' + rel + ']→  ' + (focusData.label || '');
  }}
  const tourPanel = tourStep
    ? React.createElement(
        'div',
        {{
          style: {{
            position: 'absolute', top: 10, left: 10, zIndex: 6, width: 290,
            background: '#fff', border: '1px solid #d2dae6', borderRadius: 8,
            padding: '12px 14px', fontSize: 11,
            boxShadow: '0 4px 16px rgba(0,0,0,0.14)', fontFamily: 'inherit',
          }},
        }},
        React.createElement(
          'div',
          {{ style: {{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }} }},
          React.createElement('span', {{ style: {{ fontSize: 10, fontWeight: 700, letterSpacing: '0.04em', color: '#0a2540' }} }},
            'ASISTENTE · Paso ' + (stepIdx + 1) + ' / ' + steps.length),
          React.createElement('button', {{
            onClick: exitTour, title: 'Salir del asistente',
            style: {{ border: 'none', background: 'transparent', cursor: 'pointer', fontSize: 14, color: '#64748b', lineHeight: 1 }},
          }}, '✕'),
        ),
        React.createElement('div', {{ style: {{ fontSize: 8, letterSpacing: '0.1em', textTransform: 'uppercase', opacity: 0.6 }} }},
          focusData.subtitle || ''),
        React.createElement('div', {{ style: {{ fontSize: 14, fontWeight: 700, color: '#0a2540', margin: '2px 0 5px' }} }},
          focusData.label || ''),
        React.createElement('div', {{ style: {{ fontSize: 11, color: '#374151', lineHeight: 1.45 }} }},
          focusData.description || 'Sin descripción.'),
        React.createElement('div', {{
          style: {{ fontSize: 10, color: '#475569', marginTop: 7, borderTop: '1px solid #e2e8f0', paddingTop: 7, lineHeight: 1.4 }},
        }}, '\u{{1F517}} ' + connText),
        React.createElement(
          'div',
          {{ style: {{ display: 'flex', gap: 6, marginTop: 11 }} }},
          React.createElement('button', {{
            onClick: prevStep, disabled: stepIdx <= 0,
            style: {{
              flex: 1, padding: '5px 8px', border: '1px solid #0a2540', borderRadius: 5,
              background: '#fff', color: '#0a2540', fontFamily: 'inherit',
              cursor: stepIdx <= 0 ? 'not-allowed' : 'pointer', opacity: stepIdx <= 0 ? 0.4 : 1,
            }},
          }}, '◀ Anterior'),
          React.createElement('button', {{
            onClick: nextStep, disabled: stepIdx >= steps.length - 1,
            style: {{
              flex: 1, padding: '5px 8px', border: '1px solid #0a2540', borderRadius: 5,
              background: '#0a2540', color: '#fff', fontFamily: 'inherit',
              cursor: stepIdx >= steps.length - 1 ? 'not-allowed' : 'pointer',
              opacity: stepIdx >= steps.length - 1 ? 0.4 : 1,
            }},
          }}, 'Siguiente ▶'),
        ),
      )
    : null;

  return React.createElement(
    'div',
    {{ style: {{ width: '100%', height: '100%', position: 'relative' }} }},
    toolbar,
    tourPanel,
    React.createElement(ReactFlow || RF, {{
      nodes: displayNodes,
      edges: displayEdges,
      onInit: function (inst) {{ rfInstance.current = inst; }},
      onNodesChange: onNodesChange,
      onEdgesChange: onEdgesChange,
      onEdgeClick: function (evt, edge) {{ if (!tour) setFocusEdge(edge.id); }},
      onPaneClick: function () {{ if (!tour) setFocusEdge(null); }},
      nodeTypes: nodeTypes,
      nodesDraggable: true,
      fitView: true,
      fitViewOptions: {{ padding: 0.2 }},
      minZoom: 0.05,
      maxZoom: 2.5,
      proOptions: {{ hideAttribution: true }},
    }},
      React.createElement(Background, {{ gap: 24, size: 1, color: '#e2e8f0' }}),
      React.createElement(Controls, {{ position: 'bottom-right' }}),
      React.createElement(MiniMap, {{
        position: 'bottom-left',
        zoomable: true,
        pannable: true,
        nodeColor: function (n) {{ return (TYPE_STYLES[n.type] || TYPE_STYLES.default).border; }},
      }}),
    ),
  );
}}

const container = document.getElementById('root');
createRoot(container).render(React.createElement(App));
</script>
</body>
</html>
"""
