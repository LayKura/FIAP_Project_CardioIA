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
  Trash2,
} from "lucide-react";

import "./App.css";
import { supabase } from "./lib/supabase";
import { checkBackend } from "./services/healthService";
import { analyzeECG } from "./services/ecgService";
import { saveExam, getExamHistory, deleteExamHistory } from "./services/historyService";

function App() {
  const [exam, setExam] = useState(null);
  const [previewUrl, setPreviewUrl] = useState("");
  const [backendStatus, setBackendStatus] = useState("checking");
  const [model, setModel] = useState("resnet50");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activePage, setActivePage] = useState("inicio");
  const [historyItems, setHistoryItems] = useState([]);
  const [selectedHistory, setSelectedHistory] = useState(null);
  const [historyImageUrl, setHistoryImageUrl] = useState("");
  const [session, setSession] = useState(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [authMode, setAuthMode] = useState("login");
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authError, setAuthError] = useState("");
  const [authMessage, setAuthMessage] = useState("");
  const [authBusy, setAuthBusy] = useState(false);

  useEffect(() => {
    supabase.auth.getSession().then(({ data, error }) => {
      if (error) setAuthError(error.message);
      setSession(data?.session ?? null);
      setAuthLoading(false);
    });

    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, currentSession) => {
        setSession(currentSession);
        setAuthLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

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

  useEffect(() => {
    getExamHistory()
      .then(setHistoryItems)
      .catch(() => {
        console.error("Não foi possível carregar o histórico.");
      });
  }, []);

  useEffect(() => {
    if (!selectedHistory?.image) {
      setHistoryImageUrl("");
      return;
    }

    const imageUrl = URL.createObjectURL(selectedHistory.image);
    setHistoryImageUrl(imageUrl);

    return () => URL.revokeObjectURL(imageUrl);
  }, [selectedHistory]);

  async function handleAuthSubmit(event) {
    event.preventDefault();
    setAuthError("");
    setAuthMessage("");
    setAuthBusy(true);

    try {
      if (authMode === "signup") {
        const { data, error } = await supabase.auth.signUp({
          email: authEmail,
          password: authPassword,
        });
        if (error) throw error;

        if (data.session) {
          setSession(data.session);
        } else {
          setAuthMessage("Conta criada. Confira seu e-mail para confirmar o cadastro antes de entrar.");
        }
      } else {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: authEmail,
          password: authPassword,
        });
        if (error) throw error;
        setSession(data.session);
      }
    } catch (err) {
      setAuthError(err.message || "Não foi possível autenticar. Confira seus dados.");
    } finally {
      setAuthBusy(false);
    }
  }

  async function handleDeleteHistory(id) {
    const confirmed = window.confirm("Deseja excluir este exame do histórico?");
    if (!confirmed) return;

    try {
      await deleteExamHistory(id);
      setHistoryItems((items) => items.filter((item) => item.id !== id));

      if (selectedHistory?.id === id) {
        setSelectedHistory(null);
      }
    } catch {
      alert("Não foi possível excluir o exame.");
    }
  }

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
      const { data: authData, error: authSessionError } = await supabase.auth.getSession();
      if (authSessionError || !authData.session?.access_token) {
        throw new Error("Sua sessão expirou. Entre novamente na sua conta.");
      }
      const data = await analyzeECG(exam, model, authData.session.access_token);
      setResult(data);

      try {
        const savedExam = await saveExam({
          createdAt: new Date().toISOString(),
          model: data.model || model,
          classification: data.classification || "Resultado não informado",
          probabilities: data.probabilities || {},
          image: exam,
          fileName: exam.name,
        });

        setHistoryItems((items) => [savedExam, ...items]);
      } catch (storageError) {
        console.error("Erro ao salvar o histórico:", storageError);
        setError("A análise foi concluída, mas não foi possível salvar o exame no histórico deste navegador.");
      }
    } catch (err) {
      setError(
        err.response?.data?.erro ||
          err.response?.data?.error ||
          err.message ||
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

  if (authLoading) {
    return <div className="auth-screen"><p>Verificando sua sessão...</p></div>;
  }

  if (!session) {
    return (
      <div className="auth-screen">
        <form className="auth-card" onSubmit={handleAuthSubmit}>
          <div className="auth-brand-icon"><HeartPulse size={30} /></div>
          <h1>CardioIA</h1>
          <p>{authMode === "login" ? "Entre na sua conta para acessar as análises." : "Crie sua conta para acessar o CardioIA."}</p>

          <label htmlFor="auth-email">E-mail</label>
          <input
            id="auth-email"
            type="email"
            value={authEmail}
            onChange={(event) => setAuthEmail(event.target.value)}
            placeholder="seu@email.com"
            required
          />

          <label htmlFor="auth-password">Senha</label>
          <input
            id="auth-password"
            type="password"
            value={authPassword}
            onChange={(event) => setAuthPassword(event.target.value)}
            placeholder="Sua senha"
            minLength={6}
            required
          />

          {authError && <p className="auth-error">{authError}</p>}
          {authMessage && <p className="auth-message">{authMessage}</p>}

          <button className="auth-submit" type="submit" disabled={authBusy}>
            {authBusy ? "Aguarde..." : authMode === "login" ? "Entrar" : "Criar conta"}
          </button>

          <button
            className="auth-switch"
            type="button"
            onClick={() => {
              setAuthMode(authMode === "login" ? "signup" : "login");
              setAuthError("");
              setAuthMessage("");
            }}
          >
            {authMode === "login" ? "Ainda não tem conta? Criar conta" : "Já tem conta? Entrar"}
          </button>
        </form>
      </div>
    );
  }

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
                  {Math.max(anomaly, normal).toFixed(2)}%
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
            <section className="panel history-panel">
              <div className="history-heading">
                <div>
                  <div className="section-kicker">SEUS REGISTROS</div>
                  <h1>Histórico de análises</h1>
                  <p>Consulte os exames analisados neste navegador.</p>
                </div>
                <span className="history-count">
                  {historyItems.length} {historyItems.length === 1 ? "exame" : "exames"}
                </span>
              </div>

              {historyItems.length === 0 ? (
                <div className="history-empty">
                  <History size={34} />
                  <h2>Nenhum exame registrado</h2>
                  <p>Quando você realizar uma análise, ela aparecerá aqui automaticamente.</p>
                  <button
                    className="analyze-button"
                    type="button"
                    onClick={() => setActivePage("analise")}
                  >
                    Analisar primeiro ECG
                    <ArrowRight size={18} />
                  </button>
                </div>
              ) : (
                <div className="history-list">
                  {historyItems.map((item) => (
                    <article className="history-item" key={item.id}>
                      <div className="history-item-main">
                        <div className="history-item-icon">
                          <FileImage size={22} />
                        </div>
                        <div>
                          <strong>{item.classification}</strong>
                          <span>
                            {new Date(item.createdAt).toLocaleString("pt-BR")}
                          </span>
                          <small>
                            Modelo: {(item.model || "").toUpperCase()}
                          </small>
                        </div>
                      </div>
                      <div className="history-item-actions">
                        <button
                          type="button"
                          className="history-view-button"
                          onClick={() => setSelectedHistory(item)}
                        >
                          Ver detalhes
                        </button>
                        <button
                          type="button"
                          className="history-delete-button"
                          aria-label="Excluir exame"
                          title="Excluir exame"
                          onClick={() => handleDeleteHistory(item.id)}
                        >
                          <Trash2 size={17} />
                        </button>
                      </div>
                    </article>
                  ))}
                </div>
              )}

              {selectedHistory && (
                <div className="history-detail">
                  <div className="history-detail-heading">
                    <div>
                      <div className="section-kicker">DETALHES DO REGISTRO</div>
                      <h2>{selectedHistory.classification}</h2>
                      <p>
                        {new Date(selectedHistory.createdAt).toLocaleString("pt-BR")}
                      </p>
                    </div>
                    <button
                      type="button"
                      className="history-close-button"
                      onClick={() => setSelectedHistory(null)}
                      aria-label="Fechar detalhes"
                    >
                      <X size={20} />
                    </button>
                  </div>

                  {historyImageUrl && (
                    <img
                      className="history-exam-image"
                      src={historyImageUrl}
                      alt="Imagem do eletrocardiograma analisado"
                    />
                  )}

                  <p className="history-model">
                    Modelo utilizado: {(selectedHistory.model || "").toUpperCase()}
                  </p>

                  <div className="history-probabilities">
                    <div>
                      <span>Anomalia (M)</span>
                      <strong>
                        {Number(selectedHistory.probabilities?.["Anomalia (M)"] ?? 0).toFixed(2)}%
                      </strong>
                    </div>
                    <div>
                      <span>Normal (N)</span>
                      <strong>
                        {Number(selectedHistory.probabilities?.["Normal (N)"] ?? 0).toFixed(2)}%
                      </strong>
                    </div>
                  </div>

                  <div className="result-warning">
                    <AlertCircle size={20} />
                    <p>
                      Este resultado é experimental e não constitui diagnóstico médico.
                    </p>
                  </div>
                </div>
              )}
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
