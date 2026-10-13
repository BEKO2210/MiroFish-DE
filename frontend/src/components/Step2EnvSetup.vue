<template>
  <div class="env-setup-panel">
    <div class="scroll-container">
      <!-- Schritt 01: Simulationsinstanz -->
      <div class="step-card" :class="{ 'active': phase === 0, 'completed': phase > 0 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">01</span>
            <span class="step-title">{{ $t('step2.simulationsinstanzInitialisieren') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 0" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else class="badge processing">{{ $t('common.initializing') }}</span>
          </div>
        </div>
        
        <div class="card-content">
          <p class="description">
            {{ $t('step2.neueSimulationsinstanzErstellenSimulationsweltParameterVorlageLaden') }}
          </p>

          <details v-if="simulationId" class="info-details">
            <summary>{{ $t('step2.technicalDetails') }}</summary>
          <div class="info-card">
            <div class="info-row">
              <span class="info-label">{{ $t('step2.projectId') }}</span>
              <span class="info-value mono">{{ projectData?.project_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('step2.graphId') }}</span>
              <span class="info-value mono">{{ projectData?.graph_id }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('step2.simulationId') }}</span>
              <span class="info-value mono">{{ simulationId }}</span>
            </div>
            <div class="info-row">
              <span class="info-label">{{ $t('step2.taskId') }}</span>
              <span class="info-value mono">{{ taskId || $t('step2.asynchroneAufgabeAbgeschlossen') }}</span>
            </div>
          </div>
          </details>
        </div>
      </div>

      <!-- Schritt 02: Agent-Charakter generieren -->
      <div class="step-card" :class="{ 'active': phase === 1, 'completed': phase > 1 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">02</span>
            <span class="step-title">{{ $t('step2.agentCharakterGenerieren') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 1" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else-if="phase === 1" class="badge processing">{{ prepareProgress }}%</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">
            {{ $t('step2.kontextKombinierenAutomatischToolsAufrufenUmEntitaten') }}
          </p>

          <!-- Profiles Stats -->
          <div v-if="profiles.length > 0" class="stats-grid">
            <div class="stat-card">
              <span class="stat-value">{{ profiles.length }}</span>
              <span class="stat-label">{{ $t('step2.aktuelleAgenten') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ expectedTotal || '-' }}</span>
              <span class="stat-label">{{ $t('step2.erwarteteGesamtzahl') }}</span>
            </div>
            <div class="stat-card">
              <span class="stat-value">{{ totalTopicsCount }}</span>
              <span class="stat-label">{{ $t('step2.aktuellVerknupfteThemenDerRealitatsSamen') }}</span>
            </div>
          </div>

          <!-- Profiles List Preview -->
          <div v-if="profiles.length > 0" class="profiles-preview">
            <div class="preview-header">
              <span class="preview-title">{{ $t('step2.generierteAgentCharaktere') }}</span>
            </div>
            <div class="profiles-list">
              <div 
                v-for="(profile, idx) in profiles" 
                :key="idx" 
                class="profile-card"
                @click="selectProfile(profile)"
              >
                <div class="profile-header">
                  <span class="profile-realname">{{ profile.username || $t('common.none') }}</span>
                  <span class="profile-username">@{{ profile.name || `agent_${idx}` }}</span>
                </div>
                <div class="profile-meta">
                  <span class="profile-profession">{{ profile.profession || $t('step2.unknownProfession') }}</span>
                </div>
                <p class="profile-bio">{{ profile.bio || $t('step2.keineBeschreibungVorhanden') }}</p>
                <div v-if="profile.interested_topics?.length" class="profile-topics">
                  <span 
                    v-for="topic in profile.interested_topics.slice(0, 3)" 
                    :key="topic" 
                    class="topic-tag"
                  >{{ topic }}</span>
                  <span v-if="profile.interested_topics.length > 3" class="topic-more">
                    +{{ profile.interested_topics.length - 3 }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Schritt 03: Dual-Plattform-Simulationskonfiguration generieren -->
      <div class="step-card" :class="{ 'active': phase === 2, 'completed': phase > 2 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">03</span>
            <span class="step-title">{{ $t('step2.dualPlattformSimulationskonfigurationGenerieren') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 2" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else-if="phase === 2" class="badge processing">{{ $t('common.generating') }}</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">
            {{ $t('step2.llmKonfiguriertBasierendAufSimulationsanforderungenUndRealitats') }}
          </p>
          
          <!-- Config Preview -->
          <div v-if="simulationConfig" class="config-detail-panel">
            <!-- Zeitkonfiguration -->
            <div class="config-block">
              <div class="config-grid">
                <div class="config-item">
                  <span class="config-item-label">{{ $t('step2.simulationsdauer') }}</span>
                  <span class="config-item-value">{{ simulationConfig.time_config?.total_simulation_hours || '-' }} {{ $t('step2.stunden') }}</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">{{ $t('step2.dauerProRunde') }}</span>
                  <span class="config-item-value">{{ simulationConfig.time_config?.minutes_per_round || '-' }} {{ $t('step2.minuten') }}</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">{{ $t('step2.gesamtrunden') }}</span>
                  <span class="config-item-value">{{ Math.floor((simulationConfig.time_config?.total_simulation_hours * 60 / simulationConfig.time_config?.minutes_per_round)) || '-' }} {{ $t('step2.runden') }}</span>
                </div>
                <div class="config-item">
                  <span class="config-item-label">{{ $t('step2.aktivProStunde') }}</span>
                  <span class="config-item-value">{{ simulationConfig.time_config?.agents_per_hour_min }}-{{ simulationConfig.time_config?.agents_per_hour_max }}</span>
                </div>
              </div>
              <div class="time-periods">
                <div class="period-item">
                  <span class="period-label">{{ $t('step2.hauptverkehrszeit') }}</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.peak_hours?.join(':00, ') }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.peak_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">{{ $t('step2.arbeitszeit') }}</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.work_hours?.[0] }}:00-{{ simulationConfig.time_config?.work_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.work_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">{{ $t('step2.morgenzeit') }}</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.morning_hours?.[0] }}:00-{{ simulationConfig.time_config?.morning_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.morning_activity_multiplier }}</span>
                </div>
                <div class="period-item">
                  <span class="period-label">{{ $t('step2.nebenzeit') }}</span>
                  <span class="period-hours">{{ simulationConfig.time_config?.off_peak_hours?.[0] }}:00-{{ simulationConfig.time_config?.off_peak_hours?.slice(-1)[0] }}:00</span>
                  <span class="period-multiplier">×{{ simulationConfig.time_config?.off_peak_activity_multiplier }}</span>
                </div>
              </div>
            </div>

            <!-- Agent-Konfiguration -->
            <div class="config-block">
              <div class="config-block-header">
                <span class="config-block-title">{{ $t('step2.agentKonfiguration') }}</span>
                <span class="config-block-badge">{{ simulationConfig.agent_configs?.length || 0 }} {{ $t('step2.stk') }}</span>
              </div>
              <div class="agents-cards">
                <div 
                  v-for="agent in simulationConfig.agent_configs" 
                  :key="agent.agent_id" 
                  class="agent-card"
                >
                  <!-- Kartenkopf -->
                  <div class="agent-card-header">
                    <div class="agent-identity">
                      <span class="agent-id">{{ $t('step2.agent') }} {{ agent.agent_id }}</span>
                      <span class="agent-name">{{ agent.entity_name }}</span>
                    </div>
                    <div class="agent-tags">
                      <span class="agent-type">{{ agent.entity_type }}</span>
                      <span class="agent-stance" :class="'stance-' + agent.stance">{{ agent.stance }}</span>
                    </div>
                  </div>
                  
                  <!-- Aktive-Zeitleiste -->
                  <div class="agent-timeline">
                    <span class="timeline-label">{{ $t('step2.aktiveZeitraume') }}</span>
                    <div class="mini-timeline">
                      <div 
                        v-for="hour in 24" 
                        :key="hour - 1" 
                        class="timeline-hour"
                        :class="{ 'active': agent.active_hours?.includes(hour - 1) }"
                        :title="`${hour - 1}:00`"
                      ></div>
                    </div>
                    <div class="timeline-marks">
                      <span>0</span>
                      <span>6</span>
                      <span>12</span>
                      <span>18</span>
                      <span>24</span>
                    </div>
                  </div>

                  <!-- Verhaltensparameter -->
                  <div class="agent-params">
                    <div class="param-group">
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.beitrageStd') }}</span>
                        <span class="param-value">{{ agent.posts_per_hour }}</span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.kommentareStd') }}</span>
                        <span class="param-value">{{ agent.comments_per_hour }}</span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.antwortverzogerung') }}</span>
                        <span class="param-value">{{ agent.response_delay_min }}-{{ agent.response_delay_max }}{{ $t('step2.min') }}</span>
                      </div>
                    </div>
                    <div class="param-group">
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.aktivitatsgrad') }}</span>
                        <span class="param-value with-bar">
                          <span class="mini-bar" :style="{ width: (agent.activity_level * 100) + '%' }"></span>
                          {{ (agent.activity_level * 100).toFixed(0) }}%
                        </span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.stimmungstendenz') }}</span>
                        <span class="param-value" :class="agent.sentiment_bias > 0 ? 'positive' : agent.sentiment_bias < 0 ? 'negative' : 'neutral'">
                          {{ agent.sentiment_bias > 0 ? '+' : '' }}{{ agent.sentiment_bias?.toFixed(1) }}
                        </span>
                      </div>
                      <div class="param-item">
                        <span class="param-label">{{ $t('step2.einfluss') }}</span>
                        <span class="param-value highlight">{{ agent.influence_weight?.toFixed(1) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Plattformkonfiguration -->
            <div class="config-block">
              <div class="config-block-header">
                <span class="config-block-title">{{ $t('step2.empfehlungsalgorithmusKonfiguration') }}</span>
              </div>
              <div class="platforms-grid">
                <div v-if="simulationConfig.twitter_config" class="platform-card">
                  <div class="platform-card-header">
                    <span class="platform-name">{{ $t('step2.plattform1MarktplatzFeed') }}</span>
                  </div>
                  <div class="platform-params">
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.aktualitatsgewicht') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.recency_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.popularitatsgewicht') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.popularity_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.relevanzgewicht') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.relevance_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.viralitatsschwelle') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.viral_threshold }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.echokammerStarke') }}</span>
                      <span class="param-value">{{ simulationConfig.twitter_config.echo_chamber_strength }}</span>
                    </div>
                  </div>
                </div>
                <div v-if="simulationConfig.reddit_config" class="platform-card">
                  <div class="platform-card-header">
                    <span class="platform-name">{{ $t('step2.plattform2ThemenCommunity') }}</span>
                  </div>
                  <div class="platform-params">
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.aktualitatsgewicht') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.recency_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.popularitatsgewicht') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.popularity_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.relevanzgewicht') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.relevance_weight }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.viralitatsschwelle') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.viral_threshold }}</span>
                    </div>
                    <div class="param-row">
                      <span class="param-label">{{ $t('step2.echokammerStarke') }}</span>
                      <span class="param-value">{{ simulationConfig.reddit_config.echo_chamber_strength }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- LLM-Konfigurationsableitung -->
            <div v-if="simulationConfig.generation_reasoning" class="config-block">
              <div class="config-block-header">
                <span class="config-block-title">{{ $t('step2.llmKonfigurationsableitung') }}</span>
              </div>
              <div class="reasoning-content">
                <div 
                  v-for="(reason, idx) in simulationConfig.generation_reasoning.split('|').slice(0, 2)" 
                  :key="idx" 
                  class="reasoning-item"
                >
                  <p class="reasoning-text">{{ reason.trim() }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Schritt 04: Initiale Aktivierungsorchestrierung -->
      <div class="step-card" :class="{ 'active': phase === 3, 'completed': phase > 3 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">04</span>
            <span class="step-title">{{ $t('step2.initialeAktivierungsorchestrierung') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase > 3" class="badge success">{{ $t('common.completed') }}</span>
            <span v-else-if="phase === 3" class="badge processing">{{ $t('step2.wirdOrchestriert') }}</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">
            {{ $t('step2.basierendAufDerErzahlrichtungWerdenAutomatischInitiale') }}
          </p>

          <div v-if="simulationConfig?.event_config" class="orchestration-content">
            <!-- Erzählrichtung -->
            <div class="narrative-box">
              <span class="box-label narrative-label">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" class="special-icon">
                  <path d="M12 22C17.5228 22 22 17.5228 22 12C22 6.47715 17.5228 2 12 2C6.47715 2 2 6.47715 2 12C2 17.5228 6.47715 22 12 22Z" stroke="url(#paint0_linear)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M16.24 7.76L14.12 14.12L7.76 16.24L9.88 9.88L16.24 7.76Z" fill="url(#paint0_linear)" stroke="url(#paint0_linear)" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
                  <defs>
                    <linearGradient id="paint0_linear" x1="2" y1="2" x2="22" y2="22" gradientUnits="userSpaceOnUse">
                      <stop stop-color="var(--color-brand-primary)"/>
                      <stop offset="1" stop-color="var(--color-warning-text)"/>
                    </linearGradient>
                  </defs>
                </svg>
                {{ $t('step2.erzahlerischeLeitrichtung') }}
              </span>
              <p class="narrative-text">{{ simulationConfig.event_config.narrative_direction }}</p>
            </div>

            <!-- Trendthemen -->
            <div class="topics-section">
              <span class="box-label">{{ $t('step2.initialeTrendthemen') }}</span>
              <div class="hot-topics-grid">
                <span v-for="topic in simulationConfig.event_config.hot_topics" :key="topic" class="hot-topic-tag">
                  # {{ topic }}
                </span>
              </div>
            </div>

            <!-- Initiale Beitragssequenz -->
            <div class="initial-posts-section">
              <span class="box-label">{{ $t('step2.initialeAktivierungssequenz') }}{{ simulationConfig.event_config.initial_posts.length }})</span>
              <div class="posts-timeline">
                <div v-for="(post, idx) in simulationConfig.event_config.initial_posts" :key="idx" class="timeline-item">
                  <div class="timeline-marker"></div>
                  <div class="timeline-content">
                    <div class="post-header">
                      <span class="post-role">{{ post.poster_type }}</span>
                      <span class="post-agent-info">
                        <span class="post-id">{{ $t('step2.agent') }} {{ post.poster_agent_id }}</span>
                        <span class="post-username">@{{ getAgentUsername(post.poster_agent_id) }}</span>
                      </span>
                    </div>
                    <p class="post-text">{{ post.content }}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Schritt 05: Vorbereitung abgeschlossen -->
      <div class="step-card" :class="{ 'active': phase === 4 }">
        <div class="card-header">
          <div class="step-info">
            <span class="step-num">05</span>
            <span class="step-title">{{ $t('step2.vorbereitungAbgeschlossen') }}</span>
          </div>
          <div class="step-status">
            <span v-if="phase >= 4" class="badge processing">{{ $t('common.processing') }}</span>
            <span v-else class="badge pending">{{ $t('common.pending') }}</span>
          </div>
        </div>

        <div class="card-content">
          <p class="description">{{ $t('step2.simulationsumgebungIstVorbereitetSimulationKannGestartetWerden') }}</p>
          
          <!-- Simulationsrunden-Konfiguration - Nur anzeigen wenn Konfiguration generiert und Rundenzahl berechnet -->
          <div v-if="simulationConfig && autoGeneratedRounds" class="rounds-config-section">
            <div class="rounds-header">
              <div class="header-left">
                <span class="section-title">{{ $t('step2.simulationsrundenEinstellung') }}</span>
                <span class="section-desc">{{ $t('step2.mirofishPlantAutomatischEineSimulationVon') }} <span class="desc-highlight">{{ simulationConfig?.time_config?.total_simulation_hours || '-' }}</span> {{ $t('step2.stundenRealzeitJedeRundeEntspricht') }} <span class="desc-highlight">{{ simulationConfig?.time_config?.minutes_per_round || '-' }}</span> {{ $t('step2.minutenZeitverlauf') }}</span>
              </div>
              <label class="switch-control">
                <input type="checkbox" v-model="useCustomRounds">
                <span class="switch-track"></span>
                <span class="switch-label">{{ $t('step2.benutzerdefiniert') }}</span>
              </label>
            </div>
            
            <Transition name="fade" mode="out-in">
              <div v-if="useCustomRounds" class="rounds-content custom" key="custom">
                <div class="slider-display">
                  <div class="slider-main-value">
                    <span class="val-num">{{ customMaxRounds }}</span>
                    <span class="val-unit">{{ $t('step2.runden') }}</span>
                  </div>
                  <div class="slider-meta-info">
                    <span>{{ $t('step2.bei100AgentenGeschatzteDauerCa') }} {{ Math.round(customMaxRounds * 0.6) }} {{ $t('step2.minuten') }}</span>
                  </div>
                </div>

                <div class="range-wrapper">
                  <input 
                    type="range" 
                    v-model.number="customMaxRounds" 
                    min="10" 
                    :max="autoGeneratedRounds"
                    step="5"
                    class="minimal-slider"
                    :style="{ '--percent': ((customMaxRounds - 10) / (autoGeneratedRounds - 10)) * 100 + '%' }"
                  />
                  <div class="range-marks">
                    <span>10</span>
                    <span 
                      class="mark-recommend" 
                      :class="{ active: customMaxRounds === 40 }"
                      @click="customMaxRounds = 40"
                      :style="{ position: 'absolute', left: `calc(${(40 - 10) / (autoGeneratedRounds - 10) * 100}% - 30px)` }"
                    >{{ $t('step2.text40Empfohlen') }}</span>
                    <span>{{ autoGeneratedRounds }}</span>
                  </div>
                </div>
              </div>
              
              <div v-else class="rounds-content auto" key="auto">
                <div class="auto-info-card">
                  <div class="auto-value">
                    <span class="val-num">{{ autoGeneratedRounds }}</span>
                    <span class="val-unit">{{ $t('step2.runden') }}</span>
                  </div>
                  <div class="auto-content">
                    <div class="auto-meta-row">
                      <span class="duration-badge">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                          <circle cx="12" cy="12" r="10"></circle>
                          <polyline points="12 6 12 12 16 14"></polyline>
                        </svg>
                        {{ $t('step2.bei100AgentenGeschatzteDauer') }} {{ Math.round(autoGeneratedRounds * 0.6) }} {{ $t('step2.minuten') }}
                      </span>
                    </div>
                    <div class="auto-desc">
                      <p class="highlight-tip" @click="useCustomRounds = true">{{ $t('step2.beiErstmaligerAusfuhrungWirdDringendEmpfohlenIn') }}</p>
                    </div>
                  </div>
                </div>
              </div>
            </Transition>
          </div>

          <div class="action-group dual">
            <button 
              class="action-btn secondary"
              @click="$emit('go-back')"
            >
              {{ $t('step2.zuruckZurGrapherstellung') }}
            </button>
            <button 
              class="action-btn primary"
              :disabled="phase < 4"
              @click="handleStartSimulation"
            >
              {{ $t('step2.paralleleDualweltSimulationStarten') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile Detail Modal -->
    <Transition name="modal">
      <div v-if="selectedProfile" class="profile-modal-overlay" @click.self="selectedProfile = null">
        <div class="profile-modal">
          <div class="modal-header">
          <div class="modal-header-info">
            <div class="modal-name-row">
              <span class="modal-realname">{{ selectedProfile.username }}</span>
              <span class="modal-username">@{{ selectedProfile.name }}</span>
            </div>
            <span class="modal-profession">{{ selectedProfile.profession }}</span>
          </div>
          <button class="close-btn" @click="selectedProfile = null">×</button>
        </div>
        
        <div class="modal-body">
          <!-- Grundinformationen -->
          <div class="modal-info-grid">
            <div class="info-item">
              <span class="info-label">{{ $t('step2.dargestelltesAlter') }}</span>
              <span class="info-value">{{ selectedProfile.age || '-' }} {{ $t('step2.jahre') }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('step2.dargestelltesGeschlecht') }}</span>
              <span class="info-value">{{ { male: $t('step2.mannlich'), female: $t('step2.female'), other: $t('step2.otherGender') }[selectedProfile.gender] || selectedProfile.gender }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('step2.landRegion') }}</span>
              <span class="info-value">{{ selectedProfile.country || '-' }}</span>
            </div>
            <div class="info-item">
              <span class="info-label">{{ $t('step2.dargestellterMbti') }}</span>
              <span class="info-value mbti">{{ selectedProfile.mbti || '-' }}</span>
            </div>
          </div>

          <!-- Beschreibung -->
          <div class="modal-section">
            <span class="section-label">{{ $t('step2.charakterBeschreibung') }}</span>
            <p class="section-bio">{{ selectedProfile.bio || $t('step2.keineBeschreibungVorhanden') }}</p>
          </div>

          <!-- Interessensthemen -->
          <div class="modal-section" v-if="selectedProfile.interested_topics?.length">
            <span class="section-label">{{ $t('step2.mitRealitatsSamenVerknupfteThemen') }}</span>
            <div class="topics-grid">
              <span 
                v-for="topic in selectedProfile.interested_topics" 
                :key="topic" 
                class="topic-item"
              >{{ topic }}</span>
            </div>
          </div>

          <!-- Detaillierter Charakter -->
          <div class="modal-section" v-if="selectedProfile.persona">
            <span class="section-label">{{ $t('step2.detaillierterCharakterHintergrund') }}</span>
            
            <!-- Charakter-Dimensionsübersicht -->
            <div class="persona-dimensions">
              <div class="dimension-card">
                <span class="dim-title">{{ $t('step2.gesamterlebnisDesEreignisses') }}</span>
                <span class="dim-desc">{{ $t('step2.vollstandigeVerhaltensspurInDiesemEreignis') }}</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">{{ $t('step2.verhaltensprofilierung') }}</span>
                <span class="dim-desc">{{ $t('step2.erfahrungszusammenfassungUndVerhaltensstilPraferenzen') }}</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">{{ $t('step2.einzigartigeErinnerungspragung') }}</span>
                <span class="dim-desc">{{ $t('step2.aufRealitatsSamenBasierendeErinnerungen') }}</span>
              </div>
              <div class="dimension-card">
                <span class="dim-title">{{ $t('step2.sozialesBeziehungsnetzwerk') }}</span>
                <span class="dim-desc">{{ $t('step2.individuelleVerbindungenUndInteraktionsgraph') }}</span>
              </div>
            </div>

            <div class="persona-content">
              <p class="section-persona">{{ selectedProfile.persona }}</p>
            </div>
          </div>
        </div>
      </div>
      </div>
    </Transition>

    <!-- Bottom Info / Logs -->
    <div class="system-logs">
      <div class="log-header">
        <span class="log-title">{{ $t('step2.systemubersicht') }}</span>
      </div>
      <div class="log-content" ref="logContent">
        <div class="log-line" v-for="(log, idx) in systemLogs" :key="idx">
          <span class="log-time">{{ log.time }}</span>
          <span class="log-msg">{{ log.msg }}</span>
        </div>
      </div>
    </div>
    <MobileStickyBar
      :primary-label="$t('step2.paralleleDualweltSimulationStarten')"
      :primary-disabled="phase < 4"
      :secondary-label="$t('step2.zuruckZurGrapherstellung')"
      @primary-click="handleStartSimulation"
      @secondary-click="$emit('go-back')"
    />
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { useI18n } from 'vue-i18n'
import MobileStickyBar from './MobileStickyBar.vue'
import { 
  prepareSimulation, 
  getPrepareStatus, 
  getSimulationProfilesRealtime,
  getSimulationConfig,
  getSimulationConfigRealtime 
} from '../api/simulation'

const { t } = useI18n()

const props = defineProps({
  simulationId: String,  // Von übergeordneter Komponente übergeben
  projectData: Object,
  graphData: Object,
  systemLogs: Array
})

const emit = defineEmits(['go-back', 'next-step', 'add-log', 'update-status'])

// State
const phase = ref(0) // 0: Initialisierung, 1: Charakter generieren, 2: Konfiguration generieren, 3: Abgeschlossen
const taskId = ref(null)
const prepareProgress = ref(0)
const currentStage = ref('')
const progressMessage = ref('')
const profiles = ref([])
const entityTypes = ref([])
const expectedTotal = ref(null)
const simulationConfig = ref(null)
const selectedProfile = ref(null)
const showProfilesDetail = ref(true)

// Protokoll-Deduplizierung: Letzte ausgegebene Schlüsselinformationen aufzeichnen
let lastLoggedMessage = ''
let lastLoggedProfileCount = 0
let lastLoggedConfigStage = ''

// Simulationsrunden-Konfiguration
const useCustomRounds = ref(false) // Standard: Automatisch konfigurierte Rundenzahl verwenden
const customMaxRounds = ref(40)   // Standard-Empfehlung: 40 Runden

// Watch stage to update phase
watch(currentStage, (newStage) => {
  if (newStage === 'Agent-Charakter generieren' || newStage === 'generating_profiles') {
    phase.value = 1
  } else if (newStage === 'Simulationskonfiguration generieren' || newStage === 'generating_config') {
    phase.value = 2
    // In Konfigurationsgenerierungsphase eingetreten, Konfigurationsabfrage starten
    if (!configTimer) {
      addLog(t('step2.dualPlattformSimulationskonfigurationWirdGeneriert'))
      startConfigPolling()
    }
  } else if (newStage === 'Simulationsskripte vorbereiten' || newStage === 'copying_scripts') {
    phase.value = 2 // Gehört noch zur Konfigurationsphase
  }
})

// Automatisch generierte Rundenzahl aus Konfiguration berechnen (keine hartkodierten Standardwerte)
const autoGeneratedRounds = computed(() => {
  if (!simulationConfig.value?.time_config) {
    return null // null zurückgeben wenn Konfiguration noch nicht generiert
  }
  const totalHours = simulationConfig.value.time_config.total_simulation_hours
  const minutesPerRound = simulationConfig.value.time_config.minutes_per_round
  if (!totalHours || !minutesPerRound) {
    return null // null zurückgeben wenn Konfigurationsdaten unvollständig
  }
  const calculatedRounds = Math.floor((totalHours * 60) / minutesPerRound)
  // Sicherstellen dass maximale Rundenzahl nicht unter 40 (Empfehlung), um Schieberegler-Bereichsfehler zu vermeiden
  return Math.max(calculatedRounds, 40)
})

// Polling timer
let pollTimer = null
let profilesTimer = null
let configTimer = null

// Computed
const displayProfiles = computed(() => {
  if (showProfilesDetail.value) {
    return profiles.value
  }
  return profiles.value.slice(0, 6)
})

// Benutzernamen anhand der agent_id abrufen
const getAgentUsername = (agentId) => {
  if (profiles.value && profiles.value.length > agentId && agentId >= 0) {
    const profile = profiles.value[agentId]
    return profile?.username || `agent_${agentId}`
  }
  return `agent_${agentId}`
}

// Gesamtanzahl der verknüpften Themen aller Charaktere berechnen
const totalTopicsCount = computed(() => {
  return profiles.value.reduce((sum, p) => {
    return sum + (p.interested_topics?.length || 0)
  }, 0)
})

// Methods
const addLog = (msg) => {
  emit('add-log', msg)
}

// Klick auf Simulation-starten-Schaltfläche verarbeiten
const handleStartSimulation = () => {
  // Parameter für die übergeordnete Komponente erstellen
  const params = {}
  
  if (useCustomRounds.value) {
    // Benutzerdefinierte Rundenzahl, max_rounds Parameter übergeben
    params.maxRounds = customMaxRounds.value
    addLog(t('step2.simulationGestartetBenutzerdefinierteRundenzahlRunden', { p0: customMaxRounds.value }))
  } else {
    // Benutzer wählt automatisch generierte Rundenzahl, kein max_rounds Parameter
    addLog(t('step2.simulationGestartetAutomatischKonfigurierteRundenzahlRunden', { p0: autoGeneratedRounds.value }))
  }
  
  emit('next-step', params)
}

const truncateBio = (bio) => {
  if (bio.length > 80) {
    return bio.substring(0, 80) + '...'
  }
  return bio
}

const selectProfile = (profile) => {
  selectedProfile.value = profile
}

// Simulationsvorbereitung automatisch starten
const startPrepareSimulation = async () => {
  if (!props.simulationId) {
    addLog(t('step2.fehlerSimulationidFehlt'))
    emit('update-status', 'error')
    return
  }
  
  // Ersten Schritt als abgeschlossen markieren, zweiten Schritt starten
  phase.value = 1
  addLog(t('step2.simulationsinstanzErstellt', { p0: props.simulationId }))
  addLog(t('step2.simulationsumgebungWirdVorbereitet'))
  emit('update-status', 'processing')
  
  try {
    const res = await prepareSimulation({
      simulation_id: props.simulationId,
      use_llm_for_profiles: true,
      parallel_profile_count: 5
    })
    
    if (res.success && res.data) {
      if (res.data.already_prepared) {
        addLog(t('step2.abgeschlosseneVorbereitungErkanntWirdDirektVerwendet'))
        await loadPreparedData()
        return
      }
      
      taskId.value = res.data.task_id
      addLog(t('step2.vorbereitungsaufgabeGestartet'))
      addLog(`  └─ Task ID: ${res.data.task_id}`)
      
      // Erwartete Agent-Gesamtzahl sofort setzen (aus prepare-Schnittstellen-Rückgabewert)
      if (res.data.expected_entities_count) {
        expectedTotal.value = res.data.expected_entities_count
        addLog(t('step2.entitatenAusZepGraphGelesen', { p0: res.data.expected_entities_count }))
        if (res.data.entity_types && res.data.entity_types.length > 0) {
          addLog(t('step2.entitatstypen', { p0: res.data.entity_types.join(', ') }))
        }
      }
      
      addLog(t('step2.vorbereitungsfortschrittWirdAbgefragt'))
      // Fortschrittsabfrage starten
      startPolling()
      // Echtzeit-Profile-Abruf starten
      startProfilesPolling()
    } else {
      addLog(t('step2.vorbereitungFehlgeschlagen', { p0: res.error || t('common.unknownError') }))
      emit('update-status', 'error')
    }
  } catch (err) {
      addLog(t('step2.preparationException', { error: err.message }))
    emit('update-status', 'error')
  }
}

const startPolling = () => {
  pollTimer = setInterval(pollPrepareStatus, 2000)
}

const stopPolling = () => {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

const startProfilesPolling = () => {
  profilesTimer = setInterval(fetchProfilesRealtime, 3000)
}

const stopProfilesPolling = () => {
  if (profilesTimer) {
    clearInterval(profilesTimer)
    profilesTimer = null
  }
}

const handlePrepareFailure = (message) => {
  stopPolling()
  stopProfilesPolling()
  stopConfigPolling()
  addLog(t('step2.vorbereitungFehlgeschlagen2', { p0: message || t('common.unknownError') }))
  emit('update-status', 'error')
}

const pollPrepareStatus = async () => {
  if (!taskId.value && !props.simulationId) return
  
  try {
    const res = await getPrepareStatus({
      task_id: taskId.value,
      simulation_id: props.simulationId
    })
    
    if (res.success && res.data) {
      const data = res.data
      
      // Fortschritt aktualisieren
      prepareProgress.value = data.progress || 0
      progressMessage.value = data.message || ''
      
      // Phaseninformationen analysieren und detailliertes Protokoll ausgeben
      if (data.progress_detail) {
        currentStage.value = data.progress_detail.current_stage_name || ''
        
        // Detailliertes Fortschrittsprotokoll ausgeben (Duplikate vermeiden)
        const detail = data.progress_detail
        const logKey = `${detail.current_stage}-${detail.current_item}-${detail.total_items}`
        if (logKey !== lastLoggedMessage && detail.item_description) {
          lastLoggedMessage = logKey
          const stageInfo = `[${detail.stage_index}/${detail.total_stages}]`
          if (detail.total_items > 0) {
            addLog(`${stageInfo} ${detail.current_stage_name}: ${detail.current_item}/${detail.total_items} - ${detail.item_description}`)
          } else {
            addLog(`${stageInfo} ${detail.current_stage_name}: ${detail.item_description}`)
          }
        }
      } else if (data.message) {
        // Phase aus Nachricht extrahieren
        const match = data.message.match(/\[(\d+)\/(\d+)\]\s*([^:]+)/)
        if (match) {
          currentStage.value = match[3].trim()
        }
        // Nachrichtenprotokoll ausgeben (Duplikate vermeiden)
        if (data.message !== lastLoggedMessage) {
          lastLoggedMessage = data.message
          addLog(data.message)
        }
      }
      
      // Prüfen ob abgeschlossen
      if (data.status === 'completed' || data.status === 'ready' || data.already_prepared) {
        addLog(t('step2.vorbereitungAbgeschlossen2'))
        stopPolling()
        stopProfilesPolling()
        await loadPreparedData()
      } else if (data.status === 'failed') {
        handlePrepareFailure(data.error)
      }
    }
  } catch (err) {
    console.warn(t('step2.statusabfrageFehlgeschlagen'), err)
  }
}

const fetchProfilesRealtime = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getSimulationProfilesRealtime(props.simulationId)
    
    if (res.success && res.data) {
      const prevCount = profiles.value.length
      profiles.value = res.data.profiles || []
      // Nur aktualisieren wenn API gültigen Wert zurückgibt, um vorhandene gültige Werte nicht zu überschreiben
      if (res.data.total_expected) {
        expectedTotal.value = res.data.total_expected
      }
      
      // Entitätstypen extrahieren
      const types = new Set()
      profiles.value.forEach(p => {
        if (p.entity_type) types.add(p.entity_type)
      })
      entityTypes.value = Array.from(types)
      
      // Profil-Generierungsfortschritt protokollieren (nur bei Mengenänderung)
      const currentCount = profiles.value.length
      if (currentCount > 0 && currentCount !== lastLoggedProfileCount) {
        lastLoggedProfileCount = currentCount
        const total = expectedTotal.value || '?'
        const latestProfile = profiles.value[currentCount - 1]
        const profileName = latestProfile?.name || latestProfile?.username || `Agent_${currentCount}`
        if (currentCount === 1) {
          addLog(t('step2.agentCharakterGenerierungGestartet'))
        }
          addLog(t('step2.agentCharakter', { p0: currentCount, p1: total, p2: profileName, p3: latestProfile?.profession || t('step2.unknownProfession') }))
        
        // Wenn alle generiert sind
        if (expectedTotal.value && currentCount >= expectedTotal.value) {
          addLog(t('step2.alleAgentCharaktereErfolgreichGeneriert', { p0: currentCount }))
        }
      }
    }
  } catch (err) {
    console.warn(t('step2.profileAbrufFehlgeschlagen'), err)
  }
}

// Konfigurationsabfrage
const startConfigPolling = () => {
  configTimer = setInterval(fetchConfigRealtime, 2000)
}

const stopConfigPolling = () => {
  if (configTimer) {
    clearInterval(configTimer)
    configTimer = null
  }
}

const fetchConfigRealtime = async () => {
  if (!props.simulationId) return
  
  try {
    const res = await getSimulationConfigRealtime(props.simulationId)
    
    if (res.success && res.data) {
      const data = res.data

      if (data.status === 'failed' || data.error) {
        handlePrepareFailure(data.error)
        return
      }
      
      // Konfigurationsgenerierungsphase protokollieren (Duplikate vermeiden)
      if (data.generation_stage && data.generation_stage !== lastLoggedConfigStage) {
        lastLoggedConfigStage = data.generation_stage
        if (data.generation_stage === 'generating_profiles') {
          addLog(t('step2.agentCharakterKonfigurationWirdGeneriert'))
        } else if (data.generation_stage === 'generating_config') {
          addLog(t('step2.llmWirdAufgerufenUmSimulationskonfigurationsparameterZuGenerieren'))
        }
      }
      
      // Wenn Konfiguration bereits generiert
      if (data.config_generated && data.config) {
        simulationConfig.value = data.config
        addLog(t('step2.simulationskonfigurationErfolgreichGeneriert'))

        // Detaillierte Konfigurationszusammenfassung anzeigen
        if (data.summary) {
          addLog(t('step2.agentAnzahlStk', { p0: data.summary.total_agents }))
          addLog(t('step2.simulationDuration', { hours: data.summary.simulation_hours }))
          addLog(t('step2.initialeBeitrageStk', { p0: data.summary.initial_posts_count }))
          addLog(t('step2.trendingTopics', { count: data.summary.hot_topics_count }))
          addLog(t('step2.platformConfiguration', { twitter: data.summary.has_twitter_config ? '✓' : '✗', reddit: data.summary.has_reddit_config ? '✓' : '✗' }))
        }
        
        // Zeitkonfigurationsdetails anzeigen
        if (data.config.time_config) {
          const tc = data.config.time_config
          addLog(t('step2.zeitkonfigurationMinutenProRundeInsgesamtRunden', { p0: tc.minutes_per_round, p1: Math.floor((tc.total_simulation_hours * 60) / tc.minutes_per_round) }))
        }
        
        // Ereigniskonfiguration anzeigen
        if (data.config.event_config?.narrative_direction) {
          const narrative = data.config.event_config.narrative_direction
          addLog(t('step2.erzahlrichtung', { p0: narrative.length > 50 ? narrative.substring(0, 50) + '...' : narrative }))
        }
        
        stopConfigPolling()
        phase.value = 4
        addLog(t('step2.umgebungsaufbauAbgeschlossenSimulationKannGestartetWerden'))
        emit('update-status', 'completed')
      }
    }
  } catch (err) {
    console.warn(t('step2.konfigurationsabrufFehlgeschlagen'), err)
  }
}

const loadPreparedData = async () => {
  phase.value = 2
  addLog(t('step2.vorhandeneKonfigurationsdatenWerdenGeladen'))

  // Letztmaliger Profile-Abruf
  await fetchProfilesRealtime()
  addLog(t('step2.agentCharaktereGeladen', { p0: profiles.value.length }))

  // Konfiguration abrufen (Echtzeit-Schnittstelle verwenden)
  try {
    const res = await getSimulationConfigRealtime(props.simulationId)
    if (res.success && res.data) {
      if (res.data.config_generated && res.data.config) {
        simulationConfig.value = res.data.config
        addLog(t('step2.simulationskonfigurationErfolgreichGeladen'))

        // Detaillierte Konfigurationszusammenfassung anzeigen
        if (res.data.summary) {
          addLog(t('step2.agentAnzahlStk', { p0: res.data.summary.total_agents }))
          addLog(t('step2.simulationDuration', { hours: res.data.summary.simulation_hours }))
          addLog(t('step2.initialeBeitrageStk2', { p0: res.data.summary.initial_posts_count }))
        }
        
        addLog(t('step2.umgebungsaufbauAbgeschlossenSimulationKannGestartetWerden'))
        phase.value = 4
        emit('update-status', 'completed')
      } else if (res.data.status === 'failed' || res.data.error) {
        handlePrepareFailure(res.data.error)
      } else if (res.data.is_generating) {
        // Konfiguration noch nicht generiert, Abfrage starten
        addLog(t('step2.konfigurationWirdGeneriertAbfrageGestartet'))
        startConfigPolling()
      } else {
        handlePrepareFailure(res.data.error)
      }
    }
  } catch (err) {
    handlePrepareFailure(err.message)
  }
}

// Scroll log to bottom
const logContent = ref(null)
watch(() => props.systemLogs?.length, () => {
  nextTick(() => {
    if (logContent.value) {
      logContent.value.scrollTop = logContent.value.scrollHeight
    }
  })
})

onMounted(() => {
  // Vorbereitungsprozess automatisch starten
  if (props.simulationId) {
    addLog(t('step2.schritt2UmgebungsaufbauInitialisiert'))
    startPrepareSimulation()
  }
})

onUnmounted(() => {
  stopPolling()
  stopProfilesPolling()
  stopConfigPolling()
})
</script>

<style scoped>
.env-setup-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--color-bg-surface-subtle);
  font-family: var(--font-body);
}

.scroll-container {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* Step Card */
.step-card {
  background: var(--color-bg-surface-raised);
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 8px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  border: 1px solid var(--color-border-subtle);
  transition: all 0.3s ease;
  position: relative;
}

.step-card.active {
  border-color: var(--color-brand-primary);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--color-brand-primary) 8%, transparent);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.step-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.step-num {
  font-family: var(--font-body);
  font-size: 20px;
  font-weight: 700;
  color: var(--color-border-default);
}

.step-card.active .step-num,
.step-card.completed .step-num {
  color: var(--color-text-primary);
}

.step-title {
  font-weight: 600;
  font-size: 14px;
  letter-spacing: normal;
}

.badge {
  font-size: 10px;
  padding: 4px 8px;
  border-radius: 4px;
  font-weight: 600;
  text-transform: none;
}

.badge.success { background: var(--color-success-bg); color: var(--color-success-text); }
.badge.processing { background: var(--color-brand-primary); color: var(--color-text-inverse); }
.badge.pending { background: var(--color-bg-surface-subtle); color: var(--color-text-muted); }
.badge.accent { background: var(--color-info-bg); color: var(--color-info-text); }

.card-content {
  /* No extra padding - uses step-card's padding */
}

.api-note {
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.description {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin-bottom: 16px;
}

/* Action Section */
.action-section {
  margin-top: 16px;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 600;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn.primary {
  background: var(--color-text-primary);
  color: var(--color-text-inverse);
}

.action-btn.primary:hover:not(:disabled) {
  opacity: 0.8;
}

.action-btn.secondary {
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-primary);
}

.action-btn.secondary:hover:not(:disabled) {
  background: var(--color-border-default);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-group {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

.action-group.dual {
  display: grid;
  grid-template-columns: 1fr 1fr;
}

.action-group.dual .action-btn {
  width: 100%;
}

/* Info Card */
.info-card {
  background: var(--color-bg-surface-subtle);
  border-radius: 6px;
  padding: 16px;
  margin-top: 16px;
}

.info-details summary { cursor: pointer; font-size: 13px; color: var(--color-text-muted); padding: 8px 0; min-height: 44px; display: flex; align-items: center; }
.info-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px dashed var(--color-border-default);
}

.info-row:last-child {
  border-bottom: none;
}

.info-label {
  font-size: 12px;
  color: var(--color-text-secondary);
}

.info-value {
  font-size: 13px;
  font-weight: 500;
}

.info-value.mono {
  font-family: var(--font-body);
  font-size: 12px;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  background: var(--color-bg-surface-subtle);
  padding: 16px;
  border-radius: 6px;
}

.stat-card {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
  font-family: var(--font-body);
}

.stat-label {
  font-size: 9px;
  color: var(--color-text-muted);
  text-transform: none;
  margin-top: 4px;
  display: block;
}

/* Profiles Preview */
.profiles-preview {
  margin-top: 20px;
  border-top: 1px solid var(--color-border-default);
  padding-top: 16px;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: none;
  letter-spacing: normal;
}

.profiles-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-height: 320px;
  overflow-y: auto;
  padding-right: 4px;
}

.profiles-list::-webkit-scrollbar {
  width: 4px;
}

.profiles-list::-webkit-scrollbar-thumb {
  background: var(--color-border-default);
  border-radius: 2px;
}

.profiles-list::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-strong);
}

.profile-card {
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  padding: 14px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.profile-card:hover {
  border-color: var(--color-text-muted);
  background: var(--color-bg-surface-raised);
}

.profile-header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}

.profile-realname {
  font-size: 14px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.profile-username {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-text-muted);
}

.profile-meta {
  margin-bottom: 8px;
}

.profile-profession {
  font-size: 11px;
  color: var(--color-text-secondary);
  background: var(--color-border-subtle);
  padding: 2px 8px;
  border-radius: 3px;
}

.profile-bio {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin: 0 0 10px 0;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.profile-topics {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.topic-tag {
  font-size: 10px;
  color: var(--color-info-text);
  background: var(--color-info-bg);
  padding: 2px 8px;
  border-radius: 10px;
}

.topic-more {
  font-size: 10px;
  color: var(--color-text-muted);
  padding: 2px 6px;
}

/* Config Preview */
/* Config Detail Panel */
.config-detail-panel {
  margin-top: 16px;
}

.config-block {
  margin-top: 16px;
  border-top: 1px solid var(--color-border-default);
  padding-top: 12px;
}

.config-block:first-child {
  margin-top: 0;
  border-top: none;
  padding-top: 0;
}

.config-block-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.config-block-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: none;
  letter-spacing: normal;
}

.config-block-badge {
  font-family: var(--font-body);
  font-size: 11px;
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-secondary);
  padding: 2px 8px;
  border-radius: 10px;
}

/* Config Grid */
.config-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.config-item {
  background: var(--color-bg-surface-subtle);
  padding: 12px 14px;
  border-radius: 6px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.config-item-label {
  font-size: 11px;
  color: var(--color-border-strong);
}

.config-item-value {
  font-family: var(--font-body);
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Time Periods */
.time-periods {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.period-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
  background: var(--color-bg-surface-subtle);
  border-radius: 6px;
}

.period-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted);
  min-width: 70px;
}

.period-hours {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-text-secondary);
  flex: 1;
}

.period-multiplier {
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-info-text);
  background: var(--color-info-bg);
  padding: 2px 6px;
  border-radius: 4px;
}

/* Agents Cards */
.agents-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  max-height: 400px;
  overflow-y: auto;
  padding-right: 4px;
}

.agents-cards::-webkit-scrollbar {
  width: 4px;
}

.agents-cards::-webkit-scrollbar-thumb {
  background: var(--color-border-default);
  border-radius: 2px;
}

.agents-cards::-webkit-scrollbar-thumb:hover {
  background: var(--color-border-strong);
}

.agent-card {
  background: var(--color-bg-surface-subtle);
  border: 1px solid var(--color-border-default);
  border-radius: 6px;
  padding: 14px;
  transition: all 0.2s ease;
}

.agent-card:hover {
  border-color: var(--color-text-muted);
  background: var(--color-bg-surface-raised);
}

/* Agent Card Header */
.agent-card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 14px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--color-bg-surface-subtle);
}

.agent-identity {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.agent-id {
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-border-strong);
}

.agent-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.agent-tags {
  display: flex;
  gap: 6px;
}

.agent-type {
  font-size: 10px;
  color: var(--color-text-muted);
  background: var(--color-bg-surface-subtle);
  padding: 2px 8px;
  border-radius: 4px;
}

.agent-stance {
  font-size: 10px;
  font-weight: 500;
  text-transform: none;
  padding: 2px 8px;
  border-radius: 4px;
}

.stance-neutral {
  background: var(--color-bg-surface-subtle);
  color: var(--color-text-muted);
}

.stance-supportive {
  background: var(--color-success-bg);
  color: var(--color-success-text);
}

.stance-opposing {
  background: var(--color-error-bg);
  color: var(--color-error-text);
}

.stance-observer {
  background: var(--color-brand-primary);
  color: var(--color-warning-text);
}

/* Agent Timeline */
.agent-timeline {
  margin-bottom: 14px;
}

.timeline-label {
  display: block;
  font-size: 10px;
  color: var(--color-border-strong);
  margin-bottom: 6px;
  text-transform: none;
  letter-spacing: normal;
}

.mini-timeline {
  display: flex;
  gap: 2px;
  height: 16px;
  background: var(--color-bg-surface-subtle);
  border-radius: 4px;
  padding: 3px;
}

.timeline-hour {
  flex: 1;
  background: var(--color-border-default);
  border-radius: 2px;
  transition: all 0.2s;
}

.timeline-hour.active {
  background: linear-gradient(180deg, var(--color-info-text), var(--color-info-border));
}

.timeline-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 4px;
  font-family: var(--font-body);
  font-size: 9px;
  color: var(--color-border-strong);
}

/* Agent Params */
.agent-params {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.param-group {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.param-item .param-label {
  font-size: 10px;
  color: var(--color-border-strong);
}

.param-item .param-value {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
}

.param-value.with-bar {
  display: flex;
  align-items: center;
  gap: 6px;
}

.mini-bar {
  height: 4px;
  background: linear-gradient(90deg, var(--color-info-text), var(--color-brand-primary));
  border-radius: 2px;
  min-width: 4px;
  max-width: 40px;
}

.param-value.positive {
  color: var(--color-success-text);
}

.param-value.negative {
  color: var(--color-error-text);
}

.param-value.neutral {
  color: var(--color-text-muted);
}

.param-value.highlight {
  color: var(--color-info-text);
}

/* Platforms Grid */
.platforms-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.platform-card {
  background: var(--color-bg-surface-subtle);
  padding: 14px;
  border-radius: 6px;
}

.platform-card-header {
  margin-bottom: 10px;
  padding-bottom: 8px;
  border-bottom: 1px solid var(--color-border-default);
}

.platform-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.platform-params {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.param-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.param-value {
  font-family: var(--font-body);
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-primary);
}

/* Reasoning Content */
.reasoning-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.reasoning-item {
  padding: 12px 14px;
  background: var(--color-bg-surface-subtle);
  border-radius: 6px;
}

.reasoning-text {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin: 0;
}

/* Profile Modal */
.profile-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.profile-modal {
  background: var(--color-bg-surface-raised);
  border-radius: 16px;
  width: 90%;
  max-width: 600px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 24px;
  background: var(--color-bg-surface-raised);
  border-bottom: 1px solid var(--color-border-subtle);
}

.modal-header-info {
  flex: 1;
}

.modal-name-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}

.modal-realname {
  font-size: 20px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.modal-username {
  font-family: var(--font-body);
  font-size: 13px;
  color: var(--color-text-muted);
}

.modal-profession {
  font-size: 12px;
  color: var(--color-text-secondary);
  background: var(--color-bg-surface-subtle);
  padding: 4px 10px;
  border-radius: 4px;
  display: inline-block;
  font-weight: 500;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: none;
  color: var(--color-text-muted);
  border-radius: 50%;
  font-size: 24px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  line-height: 1;
  transition: color 0.2s;
  padding: 0;
}

.close-btn:hover {
  color: var(--color-text-primary);
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
  flex: 1;
}

/* Grundinformationsraster */
.modal-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px 16px;
  margin-bottom: 32px;
  padding: 0;
  background: transparent;
  border-radius: 0;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-label {
  font-size: 11px;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
  font-weight: 600;
}

.info-value {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.info-value.mbti {
  font-family: var(--font-body);
  color: var(--color-brand-primary);
}

/* Modulbereich */
.modal-section {
  margin-bottom: 28px;
}

.section-label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: none;
  letter-spacing: normal;
  margin-bottom: 12px;
}

.section-bio {
  font-size: 14px;
  color: var(--color-text-primary);
  line-height: 1.6;
  margin: 0;
  padding: 16px;
  background: var(--color-bg-surface-subtle);
  border-radius: 6px;
  border-left: 3px solid var(--color-border-default);
}

/* Themen-Tags */
.topics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.topic-item {
  font-size: 11px;
  color: var(--color-info-text);
  background: var(--color-info-bg);
  padding: 4px 10px;
  border-radius: 12px;
  transition: all 0.2s;
  border: none;
}

.topic-item:hover {
  background: var(--color-info-border);
  color: var(--color-info-text);
}

/* Detaillierter Charakter */
.persona-dimensions {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-bottom: 16px;
}

.dimension-card {
  background: var(--color-bg-surface-subtle);
  padding: 12px;
  border-radius: 6px;
  border-left: 3px solid var(--color-border-default);
  transition: all 0.2s;
}

.dimension-card:hover {
  background: var(--color-border-subtle);
  border-left-color: var(--color-text-muted);
}

.dim-title {
  display: block;
  font-size: 12px;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 4px;
}

.dim-desc {
  display: block;
  font-size: 10px;
  color: var(--color-text-muted);
  line-height: 1.4;
}

.persona-content {
  max-height: none;
  overflow: visible;
  padding: 0;
  background: transparent;
  border: none;
  border-radius: 0;
}

.persona-content::-webkit-scrollbar {
  width: 4px;
}

.persona-content::-webkit-scrollbar-thumb {
  background: var(--color-border-default);
  border-radius: 2px;
}

.section-persona {
  font-size: 13px;
  color: var(--color-text-secondary);
  line-height: 1.8;
  margin: 0;
  text-align: justify;
}

/* System Logs */
.system-logs {
  background: var(--color-text-primary);
  color: var(--color-border-default);
  padding: 16px;
  font-family: var(--font-body);
  border-top: 1px solid var(--color-text-primary);
  flex-shrink: 0;
}

.log-header {
  display: flex;
  justify-content: space-between;
  border-bottom: 1px solid var(--color-text-primary);
  padding-bottom: 8px;
  margin-bottom: 8px;
  font-size: 10px;
  color: var(--color-text-muted);
}

.log-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 80px; /* Approx 4 lines visible */
  overflow-y: auto;
  padding-right: 4px;
}

.log-content::-webkit-scrollbar {
  width: 4px;
}

.log-content::-webkit-scrollbar-thumb {
  background: var(--color-text-primary);
  border-radius: 2px;
}

.log-line {
  font-size: 11px;
  display: flex;
  gap: 12px;
  line-height: 1.5;
}

.log-time {
  color: var(--color-text-secondary);
  min-width: 75px;
}

.log-msg {
  color: var(--color-border-strong);
  word-break: break-all;
}

/* Spinner */
.spinner-sm {
  width: 16px;
  height: 16px;
  border: 2px solid var(--color-border-default);
  border-top-color: var(--color-brand-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
/* Orchestration Content */
.orchestration-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
  margin-top: 16px;
}

.box-label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-secondary);
  text-transform: none;
  letter-spacing: normal;
  margin-bottom: 12px;
}

.narrative-box {
  background: var(--color-bg-surface-raised);
  padding: 20px 24px;
  border-radius: 12px;
  border: 1px solid var(--color-border-subtle);
  box-shadow: 0 4px 24px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  transition: all 0.3s ease;
}

.narrative-box .box-label {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--color-text-secondary);
  font-size: 13px;
  letter-spacing: normal;
  margin-bottom: 12px;
  font-weight: 600;
}

.special-icon {
  filter: drop-shadow(0 2px 4px color-mix(in srgb, var(--color-brand-primary) 20%, transparent));
  transition: transform 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.narrative-box:hover .special-icon {
  transform: rotate(180deg);
}

.narrative-text {
  font-family: var(--font-body);
  font-size: 14px;
  color: var(--color-text-primary);
  line-height: 1.8;
  margin: 0;
  text-align: justify;
  letter-spacing: normal;
}

.topics-section {
  background: var(--color-bg-surface-raised);
}

.hot-topics-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.hot-topic-tag {
  font-size: 12px;
  color:color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  background: var(--color-warning-bg);
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.hot-topic-more {
  font-size: 11px;
  color: var(--color-text-muted);
  padding: 4px 6px;
}

.initial-posts-section {
  border-top: 1px solid var(--color-border-subtle);
  padding-top: 16px;
}

.posts-timeline {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding-left: 8px;
  border-left: 2px solid var(--color-border-subtle);
  margin-top: 12px;
}

.timeline-item {
  position: relative;
  padding-left: 20px;
}

.timeline-marker {
  position: absolute;
  left: 0;
  top: 14px;
  width: 12px;
  height: 2px;
  background: var(--color-border-default);
}

.timeline-content {
  background: var(--color-bg-surface-subtle);
  padding: 12px;
  border-radius: 6px;
  border: 1px solid var(--color-border-subtle);
}

.post-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}

.post-role {
  font-size: 11px;
  font-weight: 700;
  color: var(--color-text-primary);
  text-transform: none;
}

.post-agent-info {
  display: flex;
  align-items: center;
  gap: 6px;
}

.post-id,
.post-username {
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-text-secondary);
  line-height: 1;
  vertical-align: baseline;
}

.post-username {
  margin-right: 6px;
}

.post-text {
  font-size: 12px;
  color: var(--color-text-secondary);
  line-height: 1.5;
  margin: 0;
}

/* Simulationsrunden-Konfigurationsstil */
.rounds-config-section {
  margin: 24px 0;
  padding-top: 24px;
  border-top: 1px solid var(--color-border-subtle);
}

.rounds-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.section-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text-primary);
}

.section-desc {
  font-size: 12px;
  color: var(--color-border-strong);
}

.desc-highlight {
  font-family: var(--font-body);
  font-weight: 600;
  color: var(--color-text-primary);
  background: var(--color-bg-surface-subtle);
  padding: 1px 6px;
  border-radius: 4px;
  margin: 0 2px;
}

/* Switch Control */
.switch-control {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px 4px 4px;
  border-radius: 20px;
  transition: background 0.2s;
}

.switch-control:hover {
  background: var(--color-bg-surface-subtle);
}

.switch-control input {
  display: none;
}

.switch-track {
  width: 36px;
  height: 20px;
  background: var(--color-border-default);
  border-radius: 10px;
  position: relative;
  transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.switch-track::after {
  content: '';
  position: absolute;
  left: 2px;
  top: 2px;
  width: 16px;
  height: 16px;
  background: var(--color-bg-surface-raised);
  border-radius: 50%;
  box-shadow: 0 1px 3px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  transition: transform 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
}

.switch-control input:checked + .switch-track {
  background: var(--color-text-primary);
}

.switch-control input:checked + .switch-track::after {
  transform: translateX(16px);
}

.switch-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text-muted);
}

.switch-control input:checked ~ .switch-label {
  color: var(--color-text-primary);
}

/* Slider Content */
.rounds-content {
  animation: fadeIn 0.3s ease;
}

.slider-display {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 16px;
}

.slider-main-value {
  display: flex;
  align-items: baseline;
  gap: 4px;
}

.val-num {
  font-family: var(--font-body);
  font-size: 24px;
  font-weight: 700;
  color: var(--color-text-primary);
}

.val-unit {
  font-size: 12px;
  color: var(--color-text-secondary);
  font-weight: 500;
}

.slider-meta-info {
  font-family: var(--font-body);
  font-size: 11px;
  color: var(--color-text-muted);
  background: var(--color-bg-surface-subtle);
  padding: 4px 8px;
  border-radius: 4px;
}

.range-wrapper {
  position: relative;
  padding: 0 2px;
}

.minimal-slider {
  -webkit-appearance: none;
  width: 100%;
  height: 4px;
  background: var(--color-border-default);
  border-radius: 2px;
  outline: none;
  background-image: linear-gradient(var(--color-text-primary), var(--color-text-primary));
  background-size: var(--percent, 0%) 100%;
  background-repeat: no-repeat;
  cursor: pointer;
}

.minimal-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: var(--color-bg-surface-raised);
  border: 2px solid var(--color-text-primary);
  cursor: pointer;
  box-shadow: 0 1px 4px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
  transition: transform 0.1s;
  margin-top: -6px; /* Center thumb */
}

.minimal-slider::-webkit-slider-thumb:hover {
  transform: scale(1.1);
}

.minimal-slider::-webkit-slider-runnable-track {
  height: 4px;
  border-radius: 2px;
}

.range-marks {
  display: flex;
  justify-content: space-between;
  margin-top: 8px;
  font-family: var(--font-body);
  font-size: 10px;
  color: var(--color-border-strong);
  position: relative;
}

.mark-recommend {
  cursor: pointer;
  transition: color 0.2s;
  position: relative;
}

.mark-recommend:hover {
  color: var(--color-text-primary);
}

.mark-recommend.active {
  color: var(--color-text-primary);
  font-weight: 600;
}

.mark-recommend::after {
  content: '';
  position: absolute;
  top: -12px;
  left: 50%;
  transform: translateX(-50%);
  width: 1px;
  height: 4px;
  background: var(--color-border-default);
}

/* Auto Info */
.auto-info-card {
  display: flex;
  align-items: center;
  gap: 24px;
  background: var(--color-bg-surface-subtle);
  padding: 16px 20px;
  border-radius: 8px;
}

.auto-value {
  display: flex;
  flex-direction: row;
  align-items: baseline;
  gap: 4px;
  padding-right: 24px;
  border-right: 1px solid var(--color-border-default);
}

.auto-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
  justify-content: center;
}

.auto-meta-row {
  display: flex;
  align-items: center;
}

.duration-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-family: var(--font-body);
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
  background: var(--color-bg-surface-raised);
  border: 1px solid var(--color-border-default);
  padding: 3px 8px;
  border-radius: 6px;
  box-shadow: 0 1px 2px color-mix(in srgb, var(--color-text-primary) 12%, transparent);
}

.auto-desc {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.auto-desc p {
  margin: 0;
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.highlight-tip {
  margin-top: 4px !important;
  font-size: 12px !important;
  color: var(--color-text-primary) !important;
  font-weight: 500;
  cursor: pointer;
}

.highlight-tip:hover {
  text-decoration: underline;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(4px); }
  to { opacity: 1; transform: translateY(0); }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Modal Transition */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-active .profile-modal {
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.modal-leave-active .profile-modal {
  transition: all 0.3s ease-in;
}

.modal-enter-from .profile-modal,
.modal-leave-to .profile-modal {
  transform: scale(0.95) translateY(10px);
  opacity: 0;
}
/* Mobile-first polish */
button, [role="button"], input, select, textarea { min-height: var(--touch-target-min); }
h1, h2, h3, h4, h5, h6, .step-title, .section-title { font-family: var(--font-heading); }
.env-setup-panel, .scroll-container, .step-card { min-width: 0; }
.step-card, .description, .info-value, .config-value { overflow-wrap: anywhere; }
@media (max-width: 768px) {
  .scroll-container { padding-bottom: calc(96px + env(safe-area-inset-bottom, 0px)); }
  .action-group.dual { display: none; }
  .scroll-container { padding: 16px 16px calc(80px + env(safe-area-inset-bottom)); gap: 16px; }
  .step-card { width: 100%; padding: 16px; border-radius: var(--radius-lg); }
  .card-header, .step-info, .action-group { align-items: flex-start; }
  .card-header, .action-group { flex-wrap: wrap; gap: 12px; }
  .action-btn { width: 100%; }
  .modal-overlay { padding: 16px; }
  .modal-content { width: 100%; max-width: 100%; max-height: calc(100dvh - 32px); }
  .timeline-item, .timeline-content { min-width: 0; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; transition-duration: .01ms !important; }
}
</style>
