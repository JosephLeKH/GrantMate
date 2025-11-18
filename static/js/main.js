(function () {
  'use strict';

  // Initialize year
  const yearSpan = document.getElementById('year');
  if (yearSpan) {
    yearSpan.textContent = String(new Date().getFullYear());
  }

  // Get DOM elements
  const grantForm = document.getElementById('grant-demo-form');
  const questionsTextarea = document.getElementById('grant-questions');
  const contextTextarea = document.getElementById('grant-context');
  const submitBtn = document.getElementById('submit-btn');
  const clearBtn = document.getElementById('clear-btn');
  const copyAllBtn = document.getElementById('copy-all-btn');
  const exportDocBtn = document.getElementById('export-doc-btn');
  const exportStatus = document.getElementById('export-status');
  const outputSection = document.getElementById('output-section');
  const outputContent = document.getElementById('output-content');
  const outputSubtitle = document.getElementById('output-subtitle');
  const outputBadge = document.getElementById('output-badge');
  const questionsCount = document.getElementById('questions-count');
  const toast = document.getElementById('toast');
  const toastMessage = document.getElementById('toast-message');
  const toastIcon = document.getElementById('toast-icon');

  const exportBtnDefaultContent = exportDocBtn ? exportDocBtn.innerHTML : '';
  let lastResults = [];

  // Question counter with animation
  function updateQuestionCount() {
    if (!questionsTextarea || !questionsCount) return;
    
    const text = questionsTextarea.value.trim();
    const lines = text.split('\n').filter(line => line.trim().length > 0);
    const count = lines.length;
    
    const countText = questionsCount.querySelector('.count-text');
    if (countText) {
      countText.textContent = count === 0 
        ? 'No questions' 
        : count === 1 
          ? '1 question' 
          : `${count} questions`;
      
      // Animate count change
      countText.style.transform = 'scale(1.2)';
      setTimeout(() => {
        countText.style.transform = 'scale(1)';
      }, 200);
      
      // Update color
      if (count > 0) {
        countText.style.color = 'var(--color-phc-red)';
        countText.style.fontWeight = '600';
      } else {
        countText.style.color = 'var(--color-text-muted)';
        countText.style.fontWeight = '500';
      }
    }
  }

  if (questionsTextarea) {
    questionsTextarea.addEventListener('input', updateQuestionCount);
    updateQuestionCount();
    
    // Add focus animation
    questionsTextarea.addEventListener('focus', function() {
      this.parentElement.classList.add('focused');
    });
    
    questionsTextarea.addEventListener('blur', function() {
      this.parentElement.classList.remove('focused');
    });
  }

  // Enhanced toast notification
  function showToast(message, type = 'success') {
    if (!toast || !toastMessage || !toastIcon) return;
    
    toastMessage.textContent = message;
    toastIcon.textContent = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
    toast.className = `toast show ${type}`;
    
    // Trigger animation
    setTimeout(() => {
      toast.style.transform = 'translateY(0) scale(1)';
    }, 10);
    
    setTimeout(() => {
      toast.classList.remove('show');
      toast.style.transform = 'translateY(1rem) scale(0.95)';
    }, 3000);
  }

  // Escape HTML
  function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }

  // Format answer text with enhanced styling
  function formatAnswer(text) {
    if (!text) return '';
    
    const escaped = escapeHtml(text);
    // Split by double newlines for paragraphs
      return escaped
        .split(/\n{2,}/)
      .map(paragraph => {
        if (!paragraph.trim()) return '';
        // Replace single newlines with <br>
        const formatted = paragraph.replace(/\n/g, '<br>');
        return `<p>${formatted}</p>`;
      })
        .join('');
  }

  // Copy to clipboard with enhanced feedback
  async function copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      showToast('Copied to clipboard!', 'success');
      return true;
    } catch (err) {
      console.error('Failed to copy:', err);
      showToast('Failed to copy to clipboard', 'error');
      return false;
    }
  }

  // Enhanced loading state with progress
  function renderLoading() {
    lastResults = [];
    if (exportDocBtn) {
      exportDocBtn.disabled = true;
      exportDocBtn.innerHTML = exportBtnDefaultContent;
    }
    if (exportStatus) {
      exportStatus.className = 'export-status';
      exportStatus.textContent = '';
      exportStatus.style.display = 'none';
    }

    const loadingMessages = [
      'Analyzing your questions...',
      'Searching knowledge base...',
      'Generating responses...',
      'Finalizing answers...'
    ];
    
    let messageIndex = 0;
    const updateMessage = () => {
      if (messageIndex < loadingMessages.length) {
        const loadingText = outputContent.querySelector('.loading-text');
        if (loadingText) {
          loadingText.textContent = loadingMessages[messageIndex];
        }
        messageIndex++;
      }
    };
    
    outputContent.innerHTML = `
      <div class="loading-state">
        <div class="loading-spinner"></div>
        <div class="loading-text">Analyzing your questions...</div>
        <div class="loading-subtext">
          Our AI is processing your grant questions
          <div class="loading-dots">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
        <div class="progress-bar">
          <div class="progress-fill"></div>
        </div>
      </div>
    `;
    
    outputSubtitle.textContent = 'AI is analyzing your questions and generating responses...';
    if (outputBadge) {
      outputBadge.textContent = 'Processing...';
      outputBadge.style.animation = 'pulse 1s ease-in-out infinite';
    }
    copyAllBtn.style.display = 'none';
    
    // Update loading messages
    const messageInterval = setInterval(updateMessage, 1500);
    setTimeout(() => clearInterval(messageInterval), loadingMessages.length * 1500);
  }

  // Enhanced error state
  function renderError(message) {
    if (exportDocBtn) {
      exportDocBtn.disabled = true;
      exportDocBtn.innerHTML = exportBtnDefaultContent;
    }
    if (exportStatus) {
      exportStatus.className = 'export-status error';
      exportStatus.textContent = 'An error occurred. Please try again after fixing the issue.';
    }

    outputContent.innerHTML = `
      <div class="error-state fade-in">
        <svg class="error-icon" width="64" height="64" viewBox="0 0 64 64" fill="none">
          <circle cx="32" cy="32" r="30" stroke="currentColor" stroke-width="2"/>
          <path d="M32 20V32M32 36V44" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
        </svg>
        <h3 class="error-title">Error generating answers</h3>
        <p class="error-message">${escapeHtml(message)}</p>
        <button class="btn btn-primary" onclick="location.reload()" style="margin-top: 1rem;">
          Try Again
        </button>
      </div>
    `;
    outputSubtitle.textContent = 'Please try again or check your questions';
    if (outputBadge) {
      outputBadge.textContent = 'Error';
      outputBadge.style.background = 'rgba(239, 68, 68, 0.2)';
      outputBadge.style.color = '#EF4444';
      outputBadge.style.borderColor = 'rgba(239, 68, 68, 0.3)';
    }
    copyAllBtn.style.display = 'none';
  }

  // Enhanced empty state
  function renderEmpty() {
    lastResults = [];
    if (exportDocBtn) {
      exportDocBtn.disabled = true;
      exportDocBtn.innerHTML = exportBtnDefaultContent;
    }
    if (exportStatus) {
      exportStatus.className = 'export-status';
      exportStatus.textContent = '';
      exportStatus.style.display = 'none';
    }

    outputContent.innerHTML = `
      <div class="empty-state fade-in">
        <div class="empty-icon">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
            <circle cx="32" cy="32" r="30" stroke="currentColor" stroke-width="2" stroke-dasharray="4 4" opacity="0.3"/>
            <path d="M32 20V32L40 40" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <h3>Ready to generate answers</h3>
        <p>Enter your grant questions above and click "Generate Answers" to get started.</p>
        <div style="margin-top: 1.5rem; display: flex; gap: 0.5rem; flex-wrap: wrap; justify-content: center;">
          <span class="tech-badge">AI-Powered</span>
          <span class="tech-badge">Data-Driven</span>
          <span class="tech-badge">Grant-Focused</span>
        </div>
      </div>
    `;
    outputSubtitle.textContent = 'Your AI-generated grant responses will appear here';
    if (outputBadge) {
      outputBadge.textContent = 'AI Ready';
      outputBadge.style.background = 'rgba(220, 38, 38, 0.2)';
      outputBadge.style.color = 'var(--color-phc-red-light)';
      outputBadge.style.borderColor = 'rgba(220, 38, 38, 0.3)';
    }
    copyAllBtn.style.display = 'none';
  }

  // Enhanced results rendering with staggered animations
  function renderResults(results) {
    if (!results || results.length === 0) {
      renderEmpty();
      return;
    }

    const resultsHtml = results.map((result, index) => {
      const question = escapeHtml(result.question);
      const answer = formatAnswer(result.answer);

      // Build sources section with expandable UI
      const hasSources = result.sources && result.sources.length > 0;
      const sourcesId = `sources-${index}`;
      const sourcesHtml = hasSources ? `
        <div class="answer-sources-container">
          <button 
            class="sources-toggle" 
            type="button"
            onclick="toggleSources('${sourcesId}')"
            aria-expanded="false"
            aria-controls="${sourcesId}"
          >
            <svg class="sources-icon" width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2L2 6L8 10L14 6L8 2Z" stroke="currentColor" stroke-width="1.5" fill="none"/>
              <path d="M2 10L8 14L14 10" stroke="currentColor" stroke-width="1.5" fill="none"/>
            </svg>
            <span class="sources-count">${result.sources.length} source${result.sources.length !== 1 ? 's' : ''}</span>
            <span class="sources-label">Show sources</span>
            <svg class="sources-chevron" width="14" height="14" viewBox="0 0 14 14" fill="none">
              <path d="M3.5 5.25L7 8.75L10.5 5.25" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </button>
          <div class="sources-content" id="${sourcesId}" style="display: none;">
            <div class="sources-header">
              <span class="sources-title">Knowledge Base Sources</span>
              <span class="sources-badge">AI Integrity</span>
            </div>
            <ul class="sources-list">
              ${result.sources.map(source => `
                <li class="source-item">
                  <svg class="source-icon" width="14" height="14" viewBox="0 0 14 14" fill="none">
                    <path d="M3.5 2.33333C3.5 1.8731 3.8731 1.5 4.33333 1.5H9.66667C10.1269 1.5 10.5 1.8731 10.5 2.33333V11.6667C10.5 12.1269 10.1269 12.5 9.66667 12.5H4.33333C3.8731 12.5 3.5 12.1269 3.5 11.6667V2.33333Z" stroke="currentColor" stroke-width="1.2"/>
                    <path d="M5.25 4.66667H8.75M5.25 7H8.75M5.25 9.33333H7" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
                  </svg>
                  <span class="source-text">${escapeHtml(source)}</span>
                </li>
              `).join('')}
            </ul>
          </div>
        </div>
      ` : '';
      
      return `
        <div class="answer-block" style="animation-delay: ${index * 0.1}s" tabindex="0">
          <div class="answer-header">
            <h3 class="answer-question">${question}</h3>
            <div class="answer-actions">
              <button 
                class="answer-action-btn" 
                type="button"
                onclick="copyAnswer(${index})"
                title="Copy answer"
                aria-label="Copy answer"
              >
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path d="M6 1C5.44772 1 5 1.44772 5 2V3H4C2.89543 3 2 3.89543 2 5V13C2 14.1046 2.89543 15 4 15H10C11.1046 15 12 14.1046 12 13V5C12 3.89543 11.1046 3 10 3H9V2C9 1.44772 8.55228 1 8 1H6Z" stroke="currentColor" stroke-width="1.5" fill="none"/>
                  <path d="M6 3H8V4H6V3Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
          <div class="answer-content">
            ${answer}
          </div>
          ${sourcesHtml}
        </div>
      `;
    }).join('');

    outputContent.innerHTML = resultsHtml;
    outputSubtitle.textContent = `Generated ${results.length} ${results.length === 1 ? 'answer' : 'answers'} using AI`;
    if (outputBadge) {
      outputBadge.textContent = `${results.length} Answers`;
      outputBadge.style.background = 'rgba(16, 185, 129, 0.2)';
      outputBadge.style.color = '#10B981';
      outputBadge.style.borderColor = 'rgba(16, 185, 129, 0.3)';
      outputBadge.style.animation = 'none';
    }
    copyAllBtn.style.display = 'inline-flex';

    // Store results for copy functionality
    window.currentResults = results;
    lastResults = results;
    if (exportDocBtn) {
      exportDocBtn.disabled = false;
      exportDocBtn.innerHTML = exportBtnDefaultContent;
    }
    if (exportStatus) {
      exportStatus.className = 'export-status';
      exportStatus.textContent = '';
      exportStatus.style.display = 'none';
    }

    // Scroll to top of output with smooth animation
    outputContent.scrollTo({ top: 0, behavior: 'smooth' });

    // Add fade-in animation to each block
    const blocks = outputContent.querySelectorAll('.answer-block');
    blocks.forEach((block, index) => {
      setTimeout(() => {
        block.style.opacity = '1';
        block.style.transform = 'translateY(0)';
      }, index * 100);
    });

    // Make answer blocks focusable and add keyboard navigation
    setTimeout(() => {
      blocks.forEach((block, index) => {
        block.style.outline = 'none';
        block.addEventListener('focus', function() {
          this.style.outline = '2px solid var(--color-phc-red)';
          this.style.outlineOffset = '2px';
        });
        block.addEventListener('blur', function() {
          this.style.outline = 'none';
        });
      });
    }, 100);
  }

  // Copy single answer with animation
  window.copyAnswer = function(index) {
    if (!window.currentResults || !window.currentResults[index]) return;
    
    const result = window.currentResults[index];
    const text = `${result.question}\n\n${result.answer}`;
    
    // Animate button
    const button = event.target.closest('.answer-action-btn');
    if (button) {
      button.style.transform = 'scale(0.9)';
      setTimeout(() => {
        button.style.transform = 'scale(1)';
      }, 150);
    }
    
    copyToClipboard(text);
  };

  // Copy all answers with enhanced feedback
  if (copyAllBtn) {
    copyAllBtn.addEventListener('click', () => {
      if (!window.currentResults || window.currentResults.length === 0) return;
      
      const allText = window.currentResults
        .map((result, index) => {
          return `${index + 1}. ${result.question}\n\n${result.answer}\n\n---\n`;
        })
        .join('\n');
      
      // Animate button
      copyAllBtn.style.transform = 'scale(0.95)';
      setTimeout(() => {
        copyAllBtn.style.transform = 'scale(1)';
      }, 150);
      
      copyToClipboard(allText);
    });
  }

  // Enhanced form submission with progress tracking
  if (grantForm) {
    grantForm.addEventListener('submit', async (event) => {
      event.preventDefault();

      const formData = new FormData(grantForm);
      const grantQuestions = String(formData.get('grantQuestions') || '').trim();
      const grantContext = String(formData.get('grantContext') || '').trim();

      if (!grantQuestions) {
        showToast('Please enter at least one grant question', 'error');
        questionsTextarea?.focus();
        // Add shake animation
        questionsTextarea.style.animation = 'shake 0.5s ease-in-out';
        setTimeout(() => {
          questionsTextarea.style.animation = '';
        }, 500);
        return;
      }

      // Ensure output section is visible
      if (outputSection) {
        outputSection.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }

      // Update UI with enhanced loading state
      renderLoading();
      submitBtn.disabled = true;
      const btnContent = submitBtn.querySelector('.btn-content');
      const btnLoading = submitBtn.querySelector('.btn-loading');
      if (btnContent) btnContent.style.display = 'none';
      if (btnLoading) btnLoading.style.display = 'inline-flex';

      // Add pulse animation to submit button
      submitBtn.style.animation = 'pulse 2s ease-in-out infinite';

      try {
        // Use production API endpoint
        // Configure your API URL via environment variable or use localhost
        const API_URL = window.API_URL || 'http://localhost:8000/api/generate';
        
        const response = await fetch(API_URL, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            grantQuestions: grantQuestions,
            grantContext: grantContext,
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          let errorMessage = 'Failed to generate answers';
          
          try {
            const errorData = JSON.parse(errorText);
            errorMessage = errorData.detail || errorMessage;
          } catch {
            errorMessage = errorText || errorMessage;
          }
          
          throw new Error(errorMessage);
        }

        const data = await response.json();

        if (data.results && data.results.length > 0) {
          // Add slight delay for better UX
          setTimeout(() => {
            renderResults(data.results);
            showToast(`Successfully generated ${data.results.length} ${data.results.length === 1 ? 'answer' : 'answers'}!`, 'success');
          }, 300);
        } else {
          renderError('No answers were generated. Please check your questions and try again.');
          showToast('No answers generated', 'error');
        }
      } catch (error) {
        console.error('Error generating answers:', error);
        const errorMessage = error.message || 'An unexpected error occurred';
        renderError(errorMessage);
        showToast('Failed to generate answers', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.style.animation = '';
        if (btnContent) btnContent.style.display = 'inline-flex';
        if (btnLoading) btnLoading.style.display = 'none';
      }
    });
  }

  // Enhanced clear button
  if (clearBtn) {
    clearBtn.addEventListener('click', () => {
      if (grantForm) {
        grantForm.reset();
        updateQuestionCount();
      }
      renderEmpty();
      showToast('Form cleared', 'success');
      questionsTextarea?.focus();
      
      // Add fade animation
      outputContent.style.opacity = '0.5';
      setTimeout(() => {
        outputContent.style.opacity = '1';
      }, 300);
    });
  }

  // Add smooth scroll behavior
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });

  // Add intersection observer for fade-in animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('fade-in');
        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe answer blocks when they're added
  const observeAnswers = () => {
    const answerBlocks = document.querySelectorAll('.answer-block');
    answerBlocks.forEach(block => observer.observe(block));
  };

  // Keyboard shortcuts
  document.addEventListener('keydown', (e) => {
    // Ctrl/Cmd + Enter to submit
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      if (grantForm && !submitBtn.disabled) {
        e.preventDefault();
        grantForm.dispatchEvent(new Event('submit'));
      }
    }
    
    // Escape to clear focus or close toast
    if (e.key === 'Escape') {
      if (document.activeElement === questionsTextarea || document.activeElement === contextTextarea) {
        document.activeElement.blur();
      }
      if (toast && toast.classList.contains('show')) {
        toast.classList.remove('show');
      }
    }
  });

  // Add keyboard navigation for answer blocks
  document.addEventListener('keydown', (e) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      const answerBlocks = document.querySelectorAll('.answer-block');
      if (answerBlocks.length === 0) return;
      
      const currentIndex = Array.from(answerBlocks).findIndex(block => 
        block === document.activeElement || block.contains(document.activeElement)
      );
      
      if (currentIndex === -1) {
        answerBlocks[0]?.focus();
        return;
      }
      
      const nextIndex = e.key === 'ArrowDown' 
        ? (currentIndex + 1) % answerBlocks.length
        : (currentIndex - 1 + answerBlocks.length) % answerBlocks.length;
      
      answerBlocks[nextIndex]?.focus();
      answerBlocks[nextIndex]?.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  });

  // Toggle sources visibility
  window.toggleSources = function(sourcesId) {
    const sourcesContent = document.getElementById(sourcesId);
    const toggleBtn = sourcesContent?.previousElementSibling;
    
    if (!sourcesContent || !toggleBtn) return;
    
    const isExpanded = sourcesContent.style.display !== 'none';
    sourcesContent.style.display = isExpanded ? 'none' : 'block';
    toggleBtn.setAttribute('aria-expanded', !isExpanded);
    toggleBtn.querySelector('.sources-chevron').style.transform = isExpanded ? 'rotate(0deg)' : 'rotate(180deg)';
    toggleBtn.querySelector('.sources-label').textContent = isExpanded ? 'Show sources' : 'Hide sources';
  };

  // Initialize empty state
  renderEmpty();
  
  // Observe initial state
  setTimeout(observeAnswers, 100);

  if (exportDocBtn) {
    exportDocBtn.addEventListener('click', async () => {
      if (!lastResults || lastResults.length === 0) {
        showToast('Generate answers before exporting to Google Docs', 'error');
        return;
      }

      const originalHtml = exportDocBtn.innerHTML;
      exportDocBtn.disabled = true;
      exportDocBtn.textContent = 'Creating Google Doc...';
      if (exportStatus) {
        exportStatus.className = 'export-status';
        exportStatus.textContent = 'Creating Google Doc...';
        exportStatus.style.display = 'block';
      }

      try {
        const response = await fetch('/api/export-doc', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ results: lastResults }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          let message = 'Failed to create Google Doc.';
          try {
            const data = JSON.parse(errorText);
            message = data.detail || message;
          } catch (_) {
            if (errorText) message = errorText;
          }
          throw new Error(message);
        }

        const data = await response.json();
        const docUrl = data.documentUrl;
        if (exportStatus) {
          exportStatus.className = 'export-status success';
          exportStatus.innerHTML = `Google Doc created! <a href="${docUrl}" target="_blank" rel="noopener">Open document</a>`;
          exportStatus.style.display = 'block';
        }
        showToast('Google Doc created successfully!', 'success');
      } catch (error) {
        console.error('Error exporting to Google Docs:', error);
        if (exportStatus) {
          exportStatus.className = 'export-status error';
          exportStatus.textContent = error.message || 'Failed to create Google Doc. Please try again.';
          exportStatus.style.display = 'block';
        }
        showToast('Failed to create Google Doc', 'error');
      } finally {
        exportDocBtn.disabled = false;
        exportDocBtn.innerHTML = originalHtml;
      }
    });
  }
})();
