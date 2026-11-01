// Amplia · © 2026 Heraldo Antunes · SPDX-License-Identifier: MIT
'use strict';
const $ = id => document.getElementById(id);
const token = document.querySelector('meta[name="amplia-token"]').content;
let pending = false;
let helpTrigger = 'help-open-preview';
const compact = (key, value) => key === 'dados_base64' ? '[PNG/base64 omitido apenas na exibição; presente no retorno da API]' : value;
function status(message, kind = '') { $('status').textContent = message; $('status').className = kind; }
function log(response) { $('response').textContent = JSON.stringify(response, compact, 2); }
async function command(comando, parametros = {}) {
  const response = await fetch('/api/comando', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Amplia-Token': token}, body: JSON.stringify({comando, parametros})});
  const data = await response.json();
  log(data);
  if (!data.ok) throw new Error(`${data.erro?.mensagem || 'Falha de comunicação'} [${data.erro?.codigo || response.status}]`);
  return data.resultado;
}
function showState(state) {
  const cfg = state.configuracao;
  $('width').value = Number(cfg.largura_mm.toFixed(3));
  $('height').value = Number(cfg.altura_mm.toFixed(3));
  $('margin').value = cfg.margem_mm; $('overlap').value = cfg.sobreposicao_mm;
  $('orientation').value = cfg.orientacao; $('marks').checked = cfg.marcas;
  const loaded = Boolean(state.imagem);
  $('settings').disabled = !loaded; $('export').disabled = !loaded; $('view').disabled = !loaded;
  $('metrics').hidden = !loaded; $('empty').hidden = loaded; $('preview').hidden = !loaded;
  $('image-info').textContent = loaded ? `${state.imagem.nome} · ${state.imagem.largura_px} × ${state.imagem.altura_px} px` : 'Nenhuma imagem aberta.';
  const previous = $('view').value;
  $('view').replaceChildren(new Option('Pôster completo', ''));
  if (!loaded) { $('preview').removeAttribute('src'); $('warning').textContent = ''; return; }
  const layout = state.folhas;
  for (const page of layout.folhas) $('view').add(new Option(`Folha ${page.numero} · L${page.linha} C${page.coluna}`, String(page.numero)));
  if ([...$('view').options].some(option => option.value === previous)) $('view').value = previous;
  const fmt = number => Number(number.toFixed(1)).toLocaleString('pt-BR');
  $('size-metric').textContent = `${fmt(cfg.largura_mm)} × ${fmt(cfg.altura_mm)} mm`;
  $('pages-metric').textContent = layout.total_folhas;
  $('grid-metric').textContent = `${layout.colunas} × ${layout.linhas}`;
  $('dpi-metric').textContent = `${layout.resolucao_efetiva_dpi} dpi`;
  $('warning').textContent = layout.avisos.join(' ');
}
function showPreview(result) {
  $('preview').src = `data:image/png;base64,${result.dados_base64}`;
  $('preview').hidden = false;
  $('legend').textContent = result.folha ? 'Folha A4 com margens e marcas. Áreas brancas ao final não devem ser ampliadas na impressão.' : 'Contornos indicam folhas; faixas verdes indicam sobreposição. As marcações verdes não aparecem no PDF.';
}
async function preview() {
  const args = {pixels: 1200};
  if ($('view').value) args.folha = Number($('view').value);
  showPreview(await command('previa.gerar', args));
}
function exported(result) {
  $('download').href = result.download_url;
  $('download').hidden = false;
  status(`PDF exportado: ${result.paginas} folhas A4. Salvo em ${result.caminho}`);
}
function renderHelp(help, focus = false) {
  $('assembly-help').hidden = !help.exibir;
  for (const id of ['help-open', 'help-open-preview']) $(id).setAttribute('aria-expanded', String(help.exibir));
  if (!help.exibir) { if (focus) $(helpTrigger).focus(); return; }
  const cfg = help.configuracao;
  const fmt = value => value.toLocaleString('pt-BR', {maximumFractionDigits: 3});
  $('help-title').textContent = help.titulo;
  $('help-config').textContent = `Configuração aplicada: margem ${fmt(cfg.margem_mm)} mm · sobreposição ${fmt(cfg.sobreposicao_mm)} mm · A4 ${cfg.orientacao}`;
  $('help-intro').textContent = cfg.sobreposicao_mm ? 'A faixa entre folhas contém imagem repetida. Ela permite alinhar a montagem sem perder partes do desenho.' : 'A sobreposição aplicada é zero. Não há imagem repetida para ajustar: a união será borda a borda.';
  $('help-single').hidden = !help.folha_unica;
  $('overlap-diagrams').hidden = help.modo !== 'sobrepor';
  $('edge-diagram').hidden = help.modo !== 'borda_a_borda';
  $('cut-figure').hidden = cfg.margem_mm === 0;
  $('overlap-diagrams').classList.toggle('single-diagram', cfg.margem_mm === 0);
  $('help-cut').textContent = help.passos[1].texto;
  $('help-align').textContent = help.passos[2].texto;
  $('help-edge-text').textContent = `${help.passos[1].texto} ${help.passos[2].texto}`;
  $('help-band-label').textContent = `Faixa repetida: ${fmt(cfg.sobreposicao_mm)} mm na impressão`;
  const example = help.exemplo_horizontal_mm;
  $('help-example').textContent = cfg.sobreposicao_mm ? `Exemplo horizontal para este A4: a primeira folha imprime de 0 a ${fmt(example.primeira_folha[1])} mm do pôster; a segunda começa em ${fmt(example.segunda_comeca)} mm. O trecho de ${fmt(example.faixa_repetida[0])} a ${fmt(example.faixa_repetida[1])} mm aparece nas duas folhas.` : `Exemplo horizontal: a primeira folha termina em ${fmt(example.primeira_folha[1])} mm e a segunda começa no mesmo ponto, sem faixa repetida. Para ter uma faixa de ajuste, aplique sobreposição maior que zero.`;
  $('help-steps').replaceChildren(...help.passos.map(step => {
    const item = document.createElement('li');
    const title = document.createElement('strong'); title.textContent = step.titulo;
    const text = document.createElement('p'); text.textContent = step.texto;
    item.append(title, text); return item;
  }));
  $('help-care-list').replaceChildren(...help.cuidados.map(text => { const item = document.createElement('li'); item.textContent = text; return item; }));
  $('help-preview-note').textContent = help.conceitos.previa;
  if (focus) { $('assembly-help').focus(); $('assembly-help').scrollIntoView({block:'start'}); }
}
async function refreshHelp() {
  if (!$('assembly-help').hidden) renderHelp(await command('ajuda.montagem'));
}
async function run(action) {
  if (pending) return;
  pending = true; document.body.setAttribute('aria-busy', 'true');
  status('Processando…', 'busy');
  try { await action(); } catch (error) { status(error.message, 'error'); $('response-details').open = true; }
  finally { pending = false; document.body.setAttribute('aria-busy', 'false'); }
}
async function opened(args) {
  showState(await command('imagem.abrir', args));
  $('download').hidden = true; $('view').value = '';
  await preview(); await refreshHelp(); status('Imagem aberta. Ajuste o tamanho final e confira a montagem.');
}
async function openFile(file) {
  if (!file) return;
  if (file.size > 40 * 1024 * 1024) throw new Error('A imagem excede 40 MiB.');
  status('Lendo a imagem selecionada…', 'busy');
  const data = await new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result.split(',')[1]);
    reader.onerror = () => reject(new Error('Não foi possível ler o arquivo. Tente abrir a imagem por caminho local.'));
    reader.onabort = () => reject(new Error('Leitura da imagem cancelada.'));
    reader.readAsDataURL(file);
  });
  await opened({dados_base64: data, nome: file.name});
}
$('file').addEventListener('click', () => {
  if (!pending) status('Escolha a imagem. Se o seletor do Windows não responder, pressione Esc e use o caminho local.');
});
$('file').addEventListener('cancel', () => {
  if (!pending) status('Seleção cancelada. Você pode abrir pelo caminho local ou arrastar uma imagem para a área indicada.');
});
$('file').addEventListener('change', () => run(async () => {
  try { await openFile($('file').files[0]); } finally { $('file').value = ''; }
}));
$('image-path-form').addEventListener('submit', event => {
  event.preventDefault();
  const path = $('image-path').value.trim().replace(/^"(.*)"$/, '$1');
  run(() => opened({caminho:path}));
});
for (const type of ['dragenter','dragover']) $('image-drop').addEventListener(type, event => {
  event.preventDefault(); $('image-drop').classList.add('dragging');
});
for (const type of ['dragleave','drop']) $('image-drop').addEventListener(type, () => $('image-drop').classList.remove('dragging'));
$('image-drop').addEventListener('drop', event => {
  event.preventDefault();
  const files = event.dataTransfer.files;
  run(async () => {
    if (files.length !== 1) throw new Error('Solte uma única imagem por vez.');
    await openFile(files[0]);
  });
});
document.addEventListener('dragover', event => event.preventDefault());
document.addEventListener('drop', event => {
  event.preventDefault();
  if (!$('image-drop').contains(event.target) && !pending) status('Solte a imagem na área marcada ao lado de “Sua imagem”.');
});
$('config-form').addEventListener('submit', event => { event.preventDefault(); run(async () => {
  const args = {largura_mm: Number($('width').value), altura_mm: Number($('height').value), margem_mm: Number($('margin').value), sobreposicao_mm: Number($('overlap').value), orientacao: $('orientation').value, marcas: $('marks').checked};
  showState(await command('poster.configurar', args));
  $('download').hidden = true;
  await preview(); await refreshHelp(); status('Configuração aplicada. Confira o pôster completo ou cada folha A4.');
}); });
$('config-form').addEventListener('input', () => {
  $('export').disabled = true;
  $('download').hidden = true;
  status('Há ajustes pendentes. Clique em “Aplicar e atualizar prévia” antes de exportar.');
});
$('view').addEventListener('change', () => run(async () => { await preview(); status('Prévia atualizada.'); }));
$('export').addEventListener('click', () => run(async () => {
  exported(await command('pdf.exportar', {caminho: $('pdf-path').value, substituir: $('replace').checked}));
}));
$('catalog').addEventListener('click', () => run(async () => { await command('comandos.listar'); $('response-details').open = true; status('Catálogo de comandos disponível no retorno estruturado.'); }));
for (const id of ['help-open', 'help-open-preview']) $(id).addEventListener('click', () => run(async () => {
  helpTrigger = id; renderHelp(await command('ajuda.montagem'), true); status('Ajuda de montagem aberta para a configuração aplicada.');
}));
$('help-close').addEventListener('click', () => run(async () => {
  renderHelp(await command('ajuda.montagem', {exibir:false}), true); status('Ajuda de montagem fechada.');
}));
$('command-form').addEventListener('submit', event => { event.preventDefault(); run(async () => {
  let request;
  try { request = JSON.parse($('command').value); } catch { throw new Error('Comando JSON inválido.'); }
  const response = await fetch('/api/comando', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Amplia-Token': token}, body: JSON.stringify(request)});
  const data = await response.json(); log(data); $('response-details').open = true;
  if (!data.ok) throw new Error(`${data.erro?.mensagem} [${data.erro?.codigo}]`);
  if (['imagem.abrir','poster.configurar','sessao.reiniciar'].includes(request.comando)) {
    showState(data.resultado); $('download').hidden = true;
    if (data.resultado.imagem) await preview();
    await refreshHelp();
    log(data);
  } else if (request.comando === 'previa.gerar') showPreview(data.resultado);
  else if (request.comando === 'ajuda.montagem') renderHelp(data.resultado, true);
  else if (request.comando === 'pdf.exportar') { exported(data.resultado); return; }
  status(`Comando concluído: ${request.comando}`);
}); });
$('reset').addEventListener('click', () => run(async () => {
  showState(await command('sessao.reiniciar')); $('download').hidden = true;
  await refreshHelp();
  status('Sessão reiniciada. Abra uma imagem para começar.');
}));
run(async () => {
  const state = await command('estado.obter');
  showState(state);
  if (state.imagem) {
    await preview();
    status('Sessão recuperada. A imagem e a prévia estão prontas.');
  } else status('Abra uma imagem para começar.');
});
