import { useState, useEffect } from "react";
import {
  Activity,
  HeartPulse,
  LayoutDashboard,
  FileImage,
  BrainCircuit,
  History,
  UploadCloud,
  FileCheck2,
  Wifi,
  WifiOff,
  LoaderCircle,
  AlertCircle,
  CheckCircle2,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  ArrowRight,
  X,
} from "lucide-react";

import "./App.css";
import { checkBackend } from "./services/healthService";
import { analyzeECG } from "./services/ecgService";

function App() {
  const [exam, setExam] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [backendStatus, setBackendStatus] = useState("checking");
  const [model, setModel] = useState("resnet50");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activePage, setActivePage] = useState("inicio");

  useEffect(() => {
    async function verifyBackend() {
      try {
        await checkBackend();
        setBackendStatus("online");
      } catch {
        setBackendStatus("offline");
      }
    }

    verifyBackend();
  }, []);

  function handleFileChange(event) {
    const file = event.target.files?.[0];

    if (!file) return;

    setError("");
    setResult(null);

    const validTypes = ["image/png", "image/jpeg"];

    if (!validTypes.includes(file.type)) {
      setError("Selecione uma imagem no formato PNG ou JPEG.");
      event.target.value = "";
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setError("O arquivo deve ter no máximo 10 MB.");
      event.target.value = "";
      return;
    }

    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setExam(file);
    setPreviewUrl(URL.createObjectURL(file));
  }

  function removeFile() {
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    setExam(null);
    setPreviewUrl("");
    setResult(null);
    setError("");

    const input = document.getElementById("ecg-upload");
    if (input) input.value = "";
  }

  async function handleAnalyze() {
    if (!exam) {
      setError("Selecione uma imagem de ECG antes de continuar.");
      return;
    }

    setLoading(true);
    setError("");
    setResult(null);

    try {
      const data = await analyzeECG(exam, model);
      setResult(data);
    } catch (err) {
      setError(
        err.response?.data?.erro ||
          err.response?.data?.error ||
          "Não foi possível analisar o exame. Verifique se o servidor está funcionando."
      );
    } finally {
      setLoading(false);
    }
  }

  const anomaly = Number(
    result?.probabilities?.["Anomalia (M)"] ?? 0
  );
  const normal = Number(
    result?.probabilities?.["Normal (N)"] ?? 0
  );

  const isAnomaly = result?.classification?.includes("Anomalia");

  const pageTitles = {
    inicio: "Visão geral",
    analise: "Análise de ECG",
    modelos: "Modelos de IA",
    historico: "Histórico",
  };

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <HeartPulse size={25} />
          </div>
          <div>
            <strong>CardioIA</strong>
            <span>Inteligência cardiovascular</span>
          </div>
        </div>

        <div className="sidebar-label">MENU PRINCIPAL</div>

        <nav className="sidebar-nav">
        <button
          className={`nav-item ${activePage === "inicio" ? "active" : ""}`}
          onClick={() => setActivePage("inicio")}
        >
          <LayoutDashboard size={19} />
          <span>Visão geral</span>
        </button>

        <button
          className={`nav-item ${activePage === "analise" ? "active" : ""}`}
          onClick={() => setActivePage("analise")}
        >
          <FileImage size={19} />
          <span>Análise de ECG</span>
        </button>

        <button
          className={`nav-item ${activePage === "modelos" ? "active" : ""}`}
          onClick={() => setActivePage("modelos")}
        >
          <BrainCircuit size={19} />
          <span>Modelos de IA</span>
        </button>

        <button
          className={`nav-item ${activePage === "historico" ? "active" : ""}`}
          onClick={() => setActivePage("historico")}
        >
          <History size={19} />
          <span>Histórico</span>
          <small>Em breve</small>
        </button>
      </nav>  

        <div className="sidebar-bottom">
          <div className="sidebar-security">
            <ShieldCheck size={21} />
            <div>
              <strong>Uso responsável da IA</strong>
              <p>
                Ferramenta experimental de apoio à análise de imagens.
              </p>
            </div>
          </div>

          <div className="sidebar-footer">
            <span className="footer-dot" />
            Projeto acadêmico FIAP
          </div>
        </div>
      </aside>

      <main className="main-content" id="inicio">
        <header className="topbar">
          <div className="breadcrumb">
            <span>CardioIA</span>
            <span className="breadcrumb-separator">/</span>
            <strong>{pageTitles[activePage]}</strong>
          </div>

          <div className={`connection-status ${backendStatus}`}>
            {backendStatus === "checking" && (
              <LoaderCircle size={15} className="spin" />
            )}
            {backendStatus === "online" && <Wifi size={15} />}
            {backendStatus === "offline" && <WifiOff size={15} />}

            <span>
              {backendStatus === "checking" && "Conectando ao servidor"}
              {backendStatus === "online" && "Servidor conectado"}
              {backendStatus === "offline" && "Servidor indisponível"}
            </span>
          </div>
        </header>

        <div className="page-container">
          {activePage === "inicio" && (
            <>
          <section className="welcome-section" id="inicio">
            <div>
              <div className="eyebrow">
                <Sparkles size={15} />
                PLATAFORMA DE ANÁLISE CARDIOVASCULAR
              </div>

              <h1>Visão geral</h1>

              <p>
                Utilize inteligência artificial para analisar imagens de
                eletrocardiogramas de forma experimental.
              </p>
            </div>

            <div className="welcome-illustration">
              <Activity size={48} strokeWidth={1.5} />
            </div>
          </section>

          <section className="overview-grid">
            <article className="overview-card">
              <div className="overview-icon blue">
                <FileImage size={22} />
              </div>
              <div>
                <span>Tipo de exame</span>
                <strong>Eletrocardiograma</strong>
                <small>Imagem PNG ou JPEG</small>
              </div>
            </article>

            <article className="overview-card">
              <div className="overview-icon purple">
                <BrainCircuit size={22} />
              </div>
              <div>
                <span>Modelos disponíveis</span>
                <strong>2 modelos de IA</strong>
                <small>CNN e ResNet50</small>
              </div>
            </article>

            <article className="overview-card">
              <div className="overview-icon green">
                <ShieldCheck size={22} />
              </div>
              <div>
                <span>Finalidade</span>
                <strong>Apoio experimental</strong>
                <small>Não substitui avaliação médica</small>
              </div>
            </article>
          </section>


          <section className="overview-guide">
            <div className="overview-guide-heading">
              <div>
                <div className="section-kicker">COMO FUNCIONA</div>
                <h2>Conheça o fluxo de análise</h2>
                <p>
                  O CardioIA organiza o processo em três etapas simples,
                  desde o envio da imagem até a apresentação dos resultados.
                </p>
              </div>
              <div className="overview-guide-icon">
                <HeartPulse size={27} />
              </div>
            </div>

            <div className="overview-steps">
              <article className="overview-step">
                <span className="step-number">01</span>
                <div className="overview-step-icon"><UploadCloud size={21} /></div>
                <h3>Envio do exame</h3>
                <p>Selecione uma imagem de eletrocardiograma em PNG ou JPEG.</p>
              </article>

              <article className="overview-step">
                <span className="step-number">02</span>
                <div className="overview-step-icon"><BrainCircuit size={21} /></div>
                <h3>Processamento por IA</h3>
                <p>Escolha entre os modelos CNN e ResNet50 para a classificação.</p>
              </article>

              <article className="overview-step">
                <span className="step-number">03</span>
                <div className="overview-step-icon"><Activity size={21} /></div>
                <h3>Resultado</h3>
                <p>Consulte a classificação experimental e os valores retornados.</p>
              </article>
            </div>

            <div className="overview-guide-action">
              <div>
                <strong>Pronto para começar?</strong>
                <span>Envie uma imagem e conheça a ferramenta na prática.</span>
              </div>
              <button
                className="analyze-button"
                type="button"
                onClick={() => setActivePage("analise")}
              >
                Iniciar análise
                <ArrowRight size={18} />
              </button>
            </div>
          </section>

            </>
          )}

          {activePage === "analise" && (
            <>
          <section className="workspace-grid" id="analise">
            <div className="panel upload-panel">
              <div className="panel-heading">
                <div>
                  <div className="section-kicker">ANÁLISE DE EXAME</div>
                  <h2>Enviar eletrocardiograma</h2>
                  <p>
                    Selecione uma imagem para iniciar o processamento.
                  </p>
                </div>

                <div className="heading-icon">
                  <UploadCloud size={22} />
                </div>
              </div>

              {!exam ? (
                <label className="upload-area" htmlFor="ecg-upload">
                  <div className="upload-icon">
                    <UploadCloud size={30} />
                  </div>
                  <strong>Escolha uma imagem de ECG</strong>
                  <span>
                    Clique aqui para procurar um arquivo no seu dispositivo.
                  </span>
                  <small>PNG ou JPEG · Máximo de 10 MB</small>
                  <span className="upload-button">
                    Selecionar arquivo
                    <ArrowRight size={16} />
                  </span>
                </label>
              ) : (
                <div className="preview-area">
                  <div className="preview-header">
                    <div>
                      <FileCheck2 size={19} />
                      <strong>Imagem selecionada</strong>
                    </div>
                    <button
                      className="remove-file"
                      type="button"
                      onClick={removeFile}
                      aria-label="Remover arquivo"
                    >
                      <X size={18} />
                    </button>
                  </div>

                  <div className="image-preview">
                    <img src={previewUrl} alt="Prévia do eletrocardiograma" />
                  </div>

                  <div className="file-details">
                    <strong>{exam.name}</strong>
                    <span>
                      {(exam.size / (1024 * 1024)).toFixed(2)} MB
                    </span>
                  </div>
                </div>
              )}

              <input
                id="ecg-upload"
                type="file"
                accept="image/png,image/jpeg"
                onChange={handleFileChange}
                hidden
              />

              <div className="model-section" id="modelos">
                <div className="model-heading">
                  <div>
                    <h3>Modelo de inteligência artificial</h3>
                    <p>Escolha o modelo que deseja utilizar.</p>
                  </div>
                  <BrainCircuit size={20} />
                </div>

                <div className="model-options">
                  <button
                    type="button"
                    className={`model-option ${
                      model === "resnet50" ? "selected" : ""
                    }`}
                    onClick={() => setModel("resnet50")}
                  >
                    <div className="model-option-top">
                      <span className="model-radio" />
                      <span className="model-tag">DEEP LEARNING</span>
                    </div>
                    <strong>ResNet50</strong>
                    <small>Rede neural convolucional pré-treinada.</small>
                  </button>

                  <button
                    type="button"
                    className={`model-option ${
                      model === "cnn" ? "selected" : ""
                    }`}
                    onClick={() => setModel("cnn")}
                  >
                    <div className="model-option-top">
                      <span className="model-radio" />
                      <span className="model-tag">DEEP LEARNING</span>
                    </div>
                    <strong>CNN</strong>
                    <small>Rede neural convolucional desenvolvida no projeto.</small>
                  </button>
                </div>
              </div>

              {error && (
                <div className="error-message">
                  <AlertCircle size={19} />
                  <span>{error}</span>
                </div>
              )}

              <button
                type="button"
                className="analyze-button"
                onClick={handleAnalyze}
                disabled={!exam || loading || backendStatus !== "online"}
              >
                {loading ? (
                  <>
                    <LoaderCircle size={19} className="spin" />
                    Processando exame...
                  </>
                ) : (
                  <>
                    <Activity size={19} />
                    Analisar eletrocardiograma
                    <ArrowRight size={18} />
                  </>
                )}
              </button>

              {backendStatus !== "online" && (
                <p className="backend-hint">
                  {backendStatus === "checking"
                    ? "Aguardando conexão com o servidor..."
                    : "Inicie o servidor Flask para habilitar a análise."}
                </p>
              )}
            </div>

            <aside className="panel information-panel">
              <div className="info-icon">
                <Stethoscope size={23} />
              </div>

              <h2>Sobre a análise</h2>
              <p>
                O CardioIA utiliza modelos de aprendizado profundo para
                identificar padrões em imagens de eletrocardiogramas.
              </p>

              <div className="info-divider" />

              <div className="info-point">
                <CheckCircle2 size={18} />
                <div>
                  <strong>Processamento por IA</strong>
                  <span>
                    A imagem é enviada ao modelo selecionado para classificação.
                  </span>
                </div>
              </div>

              <div className="info-point">
                <CheckCircle2 size={18} />
                <div>
                  <strong>Resultados apresentados</strong>
                  <span>
                    A resposta inclui a classificação e os valores de confiança
                    retornados pelo modelo.
                  </span>
                </div>
              </div>

              <div className="responsible-note">
                <ShieldCheck size={19} />
                <p>
                  <strong>Atenção:</strong> os resultados são experimentais e
                  não constituem diagnóstico médico.
                </p>
              </div>
            </aside>
          </section>

          {result && (
            <section className="panel results-panel" id="resultado">
              <div className="results-heading">
                <div>
                  <div className="section-kicker">PROCESSAMENTO CONCLUÍDO</div>
                  <h2>Resultado da análise</h2>
                  <p>Confira os dados retornados pelo modelo de IA.</p>
                </div>

                <div className="result-success">
                  <CheckCircle2 size={17} />
                  Análise concluída
                </div>
              </div>

              <div className="result-summary">
                <div className="result-main-icon">
                  <HeartPulse size={28} />
                </div>
                <div>
                  <span>Classificação retornada</span>
                  <strong className={isAnomaly ? "anomaly-text" : "normal-text"}>
                    {result.classification || "Resultado não informado"}
                  </strong>
                  <small>
                    Modelo utilizado: {result.model || model}
                  </small>
                </div>
              </div>

              <div className="confidence-card">
                <span>Confiança retornada pelo modelo</span>
                <strong>
                  {Number(result.confidence ?? 0).toFixed(2)}%
                </strong>
              </div>

              <div className="probability-section">
                <h3>Distribuição das classificações</h3>

                <div className="probability-item">
                  <div className="probability-label">
                    <span>Anomalia (M)</span>
                    <strong>{anomaly.toFixed(2)}%</strong>
                  </div>
                  <div className="progress-track">
                    <div
                      className="progress-fill anomaly-fill"
                      style={{ width: `${Math.min(Math.max(anomaly, 0), 100)}%` }}
                    />
                  </div>
                </div>

                <div className="probability-item">
                  <div className="probability-label">
                    <span>Normal (N)</span>
                    <strong>{normal.toFixed(2)}%</strong>
                  </div>
                  <div className="progress-track">
                    <div
                      className="progress-fill normal-fill"
                      style={{ width: `${Math.min(Math.max(normal, 0), 100)}%` }}
                    />
                  </div>
                </div>
              </div>

              <div className="result-warning">
                <AlertCircle size={20} />
                <p>
                  <strong>Importante:</strong> este resultado é experimental.
                  A confiança do modelo não representa a probabilidade clínica
                  de uma doença. A análise não substitui avaliação,
                  interpretação ou diagnóstico realizado por um profissional
                  de saúde.
                </p>
              </div>
            </section>
          )}

            </>
          )}

          {activePage === "modelos" && (
            <section className="content-page">
              <div className="welcome-section">
                <div>
                  <div className="eyebrow">
                    <BrainCircuit size={15} />
                    INTELIGÊNCIA ARTIFICIAL
                  </div>
                  <h1>Modelos de IA</h1>
                  <p>
                    Conheça os modelos de aprendizado profundo utilizados
                    pelo CardioIA na classificação experimental de imagens
                    de eletrocardiogramas.
                  </p>
                </div>
                <div className="welcome-illustration">
                  <BrainCircuit size={48} strokeWidth={1.5} />
                </div>
              </div>

              <div className="model-detail-grid">
                <article className="panel model-detail-card">
                  <div className="overview-icon purple">
                    <BrainCircuit size={24} />
                  </div>
                  <div className="section-kicker">DEEP LEARNING</div>
                  <h2>ResNet50</h2>
                  <p>
                    Arquitetura de rede neural convolucional com
                    conexões residuais. Neste projeto, é utilizada
                    para extrair características das imagens de ECG
                    e realizar a classificação.
                  </p>
                  <div className="model-detail-footer">
                    <span>Modelo disponível</span>
                    <CheckCircle2 size={18} />
                  </div>
                  <button
                    className="analyze-button"
                    type="button"
                    onClick={() => {
                      setModel("resnet50");
                      setActivePage("analise");
                    }}
                  >
                    Utilizar ResNet50
                    <ArrowRight size={18} />
                  </button>
                </article>

                <article className="panel model-detail-card">
                  <div className="overview-icon blue">
                    <Activity size={24} />
                  </div>
                  <div className="section-kicker">DEEP LEARNING</div>
                  <h2>CNN</h2>
                  <p>
                    Rede neural convolucional desenvolvida no projeto.
                    Utiliza camadas de convolução para identificar
                    padrões e características presentes nas imagens
                    de eletrocardiogramas.
                  </p>
                  <div className="model-detail-footer">
                    <span>Modelo disponível</span>
                    <CheckCircle2 size={18} />
                  </div>
                  <button
                    className="analyze-button"
                    type="button"
                    onClick={() => {
                      setModel("cnn");
                      setActivePage("analise");
                    }}
                  >
                    Utilizar CNN
                    <ArrowRight size={18} />
                  </button>
                </article>
              </div>

              <div className="responsible-note">
                <ShieldCheck size={19} />
                <p>
                  Os modelos são utilizados para fins acadêmicos e
                  experimentais. Suas classificações não constituem
                  diagnóstico médico.
                </p>
              </div>
            </section>
          )}

          {activePage === "historico" && (
            <section className="panel coming-soon-panel">
              <div className="info-icon">
                <History size={28} />
              </div>
              <div className="section-kicker">FUNCIONALIDADE EM DESENVOLVIMENTO</div>
              <h1>Histórico de análises</h1>
              <p>
                Aqui ficarão disponíveis os registros das análises
                realizadas no CardioIA.
              </p>
              <p>
                A funcionalidade de armazenamento e consulta do
                histórico ainda não foi implementada.
              </p>
              <button
                className="analyze-button"
                type="button"
                onClick={() => setActivePage("analise")}
              >
                Ir para análise de ECG
                <ArrowRight size={18} />
              </button>
            </section>
          )}

          <footer className="page-footer">
            <span>CardioIA · Projeto acadêmico FIAP</span>
            <span>Inteligência artificial aplicada à saúde</span>
          </footer>
        </div>
      </main>
    </div>
  );
}

export default App;
