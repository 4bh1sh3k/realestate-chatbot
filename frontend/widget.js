/**
 * 🏠 APEX HORIZON REALTY - AI CHATBOT WIDGET CONTROLLER
 * This script manages the user interactions, drawer toggles, and handles
 * the Server-Sent Events (SSE) stream connection to the FastAPI RAG backend.
 */

// API Configuration
const BACKEND_URL = "http://localhost:8000";

// Chat memory state
let chatHistory = [];
let isGenerating = false;

// DOM Elements
const chatDrawer = document.getElementById("chatDrawer");
const chatMessages = document.getElementById("chatMessages");
const chatForm = document.getElementById("chatForm");
const chatInputField = document.getElementById("chatInputField");
const chatTrigger = document.getElementById("chatTrigger");
const heroSearchInput = document.getElementById("heroSearchInput");
const heroSearchBtn = document.getElementById("heroSearchBtn");

/**
 * Toggles the chat drawer view
 * @param {boolean} force - optionally force drawer open (true) or closed (false)
 */
function toggleChat(force) {
    const isOpen = chatDrawer.classList.contains("open");
    const shouldOpen = (force !== undefined) ? force : !isOpen;

    if (shouldOpen) {
        chatDrawer.classList.open = true;
        chatDrawer.classList.add("open");
        
        // Hide notification badge once opened
        const badge = chatTrigger.querySelector(".notification-badge");
        if (badge) badge.classList.add("hidden");
        
        // Switch trigger button icons
        chatTrigger.querySelector(".text-icon").classList.add("hidden");
        chatTrigger.querySelector(".close-icon").classList.remove("hidden");
        
        // Focus the input box
        setTimeout(() => chatInputField.focus(), 300);
    } else {
        chatDrawer.classList.remove("open");
        chatTrigger.querySelector(".text-icon").classList.remove("hidden");
        chatTrigger.querySelector(".close-icon").classList.add("hidden");
    }
}

/**
 * Appends a message bubble into the chat interface
 * @param {string} sender - "user" or "bot"
 * @param {string} text - message text content
 * @returns {HTMLElement} - reference to the newly created text bubble element
 */
function appendMessage(sender, text) {
    const msgBubble = document.createElement("div");
    msgBubble.className = `msg-bubble ${sender}`;

    const contentDiv = document.createElement("div");
    contentDiv.className = "message-content";
    contentDiv.innerHTML = formatMessageText(text);
    msgBubble.appendChild(contentDiv);

    const timestamp = document.createElement("span");
    const now = new Date();
    timestamp.className = "msg-timestamp";
    timestamp.textContent = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    msgBubble.appendChild(timestamp);

    chatMessages.appendChild(msgBubble);
    scrollToBottom();
    return msgBubble;
}

/**
 * Formats message text, replacing special property citations with interactive badges
 * e.g., transforms "[ID: prop_001]" into a styled HTML badge.
 */
function formatMessageText(text) {
    // Escape standard HTML first to prevent XSS
    let escaped = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
    
    // Replace markdown bold (**bold**) with <strong>
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

    // Replace [ID: prop_xxx] references with an interactive badge
    const badgeRegex = /\[ID:\s*(prop_\d+)\]/g;
    return escaped.replace(badgeRegex, (match, propId) => {
        return `<span class="prop-badge" onclick="queryProperty('${propId}')"><i class="fa-solid fa-house-circle-check"></i> ${propId}</span>`;
    });
}

/**
 * Creates and appends a typing indicator bubble
 * @returns {HTMLElement} - typing indicator element
 */
function appendTypingIndicator() {
    const indicator = document.createElement("div");
    indicator.className = "msg-bubble bot typing-indicator-bubble";
    
    const content = document.createElement("div");
    content.className = "message-content";
    
    const typing = document.createElement("div");
    typing.className = "typing-indicator";
    typing.innerHTML = `
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
        <span class="typing-dot"></span>
    `;
    
    content.appendChild(typing);
    indicator.appendChild(content);
    chatMessages.appendChild(indicator);
    scrollToBottom();
    return indicator;
}

/**
 * Smoothly scrolls the messages container to the bottom
 */
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

/**
 * Initiates an automated query for a specific property badge
 * @param {string} propId - Property ID to ask about
 */
function queryProperty(propId) {
    const propertyNames = {
        "prop_001": "Modern 3-Bedroom Family Townhouse",
        "prop_002": "Luxury 4-Bedroom Villa with Ocean View",
        "prop_003": "Cozy 1-Bedroom Downtown Loft",
        "prop_004": "Suburban 2-Bedroom Home with Backyard",
        "prop_005": "Spacious 5-Bedroom Estate with Guest House"
    };
    
    const name = propertyNames[propId] || propId;
    askAIChat(`Can you give me the full details of ${name}?`);
}

/**
 * Public function to set user text and trigger a response from anywhere on the landing page
 */
function askAIChat(queryText) {
    toggleChat(true);
    submitChatQuery(queryText);
}

/**
 * Form Submit handler
 */
function handleChatSubmit(event) {
    event.preventDefault();
    const query = chatInputField.value.trim();
    if (!query || isGenerating) return;

    chatInputField.value = "";
    submitChatQuery(query);
}

/**
 * Submits a chat query, updates UI, and manages SSE streaming parsing
 */
async function submitChatQuery(message) {
    if (isGenerating) return;
    isGenerating = true;

    // 1. Show user message
    appendMessage("user", message);

    // 2. Add bot bubble with typing indicator
    const typingIndicator = appendTypingIndicator();

    // 3. Setup message holder for the incoming stream
    let botBubble = null;
    let botContentDiv = null;
    let accumulatedText = "";
    let matchingProperties = [];

    try {
        // Send request to FastAPI backend
        const response = await fetch(`${BACKEND_URL}/api/chat`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                query: message,
                history: chatHistory
            })
        });

        // Remove typing indicator as stream starts
        typingIndicator.remove();

        if (!response.ok) {
            appendMessage("bot", "⚠️ Server error: Could not reach the chatbot endpoint. Please make sure the FastAPI server is running.");
            isGenerating = false;
            return;
        }

        // Initialize Reader to parse stream chunk-by-chunk
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            // Decode bytes to string
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");

            // Save the last potentially partial line back to buffer
            buffer = lines.pop();

            for (const line of lines) {
                const cleanedLine = line.trim();
                if (!cleanedLine.startsWith("data: ")) continue;

                // Parse SSE payload
                const dataString = cleanedLine.slice(6);
                try {
                    const payload = JSON.parse(dataString);
                    
                    if (payload.type === "context") {
                        // Capture properties matching the search
                        matchingProperties = payload.properties || [];
                    } 
                    else if (payload.type === "text") {
                        const newText = payload.text || "";
                        accumulatedText += newText;

                        // Create bot message bubble if not already done
                        if (!botBubble) {
                            botBubble = document.createElement("div");
                            botBubble.className = "msg-bubble bot";
                            
                            botContentDiv = document.createElement("div");
                            botContentDiv.className = "message-content";
                            botBubble.appendChild(botContentDiv);
                            
                            const timestamp = document.createElement("span");
                            timestamp.className = "msg-timestamp";
                            timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                            botBubble.appendChild(timestamp);
                            
                            chatMessages.appendChild(botBubble);
                        }

                        // Stream typing output live
                        botContentDiv.innerHTML = formatMessageText(accumulatedText);
                        scrollToBottom();
                    } 
                    else if (payload.type === "error") {
                        appendMessage("bot", `❌ Error: ${payload.message}`);
                    }
                } catch (parseError) {
                    console.error("JSON parsing error: ", parseError);
                }
            }
        }

        // 4. Once streaming is complete, append the RAG Citation Cards if properties were found
        if (matchingProperties.length > 0 && botBubble) {
            renderCitationRow(botBubble, matchingProperties);
        }

        // 5. Append this exchange into our chat memory structure
        chatHistory.push({ role: "user", content: message });
        chatHistory.push({ role: "model", content: accumulatedText });

        // Limit chat memory history to last 10 messages for simplicity & token limit safety
        if (chatHistory.length > 10) {
            chatHistory = chatHistory.slice(chatHistory.length - 10);
        }

    } catch (err) {
        typingIndicator.remove();
        console.error(err);
        appendMessage("bot", "❌ Network Error: Failed to connect to the backend server. Please verify uvicorn is running on port 8000.");
    } finally {
        isGenerating = false;
        scrollToBottom();
    }
}

/**
 * Creates and injects a list of visual property recommendation cards below the bot message
 * @param {HTMLElement} botBubble - The bot message bubble container
 * @param {Array} properties - List of matching properties from vector retrieval
 */
function renderCitationRow(botBubble, properties) {
    const citationContainer = document.createElement("div");
    citationContainer.className = "citation-container";
    
    const title = document.createElement("div");
    title.className = "citation-title-text";
    title.innerHTML = `<i class="fa-solid fa-list-check"></i> Matching Listings (${properties.length})`;
    citationContainer.appendChild(title);

    const citationRow = document.createElement("div");
    citationRow.className = "citation-row";

    properties.forEach(prop => {
        const card = document.createElement("div");
        card.className = "mini-prop-card";
        card.onclick = () => {
            // Trigger detailed query for this card when clicked
            askAIChat(`Show details for ${prop.title}`);
        };

        card.innerHTML = `
            <div class="mini-prop-title">${prop.title}</div>
            <div class="mini-prop-price">$${prop.price.toLocaleString()}</div>
            <div class="mini-prop-meta">
                <span><i class="fa-solid fa-bed"></i> ${prop.bedrooms} Beds</span>
                <span><i class="fa-solid fa-bath"></i> ${prop.bathrooms} Baths</span>
            </div>
        `;
        citationRow.appendChild(card);
    });

    citationContainer.appendChild(citationRow);
    botBubble.appendChild(citationContainer);
    scrollToBottom();
}

// Hero Search bar triggers chatbot
if (heroSearchInput && heroSearchBtn) {
    const handleHeroSearch = () => {
        const queryText = heroSearchInput.value.trim();
        if (!queryText) return;
        heroSearchInput.value = "";
        askAIChat(queryText);
    };

    heroSearchBtn.addEventListener("click", handleHeroSearch);
    heroSearchInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") handleHeroSearch();
    });
}
