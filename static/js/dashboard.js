document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const setWebhookBtn = document.getElementById('setWebhookBtn');
    const getWebhookInfoBtn = document.getElementById('getWebhookInfoBtn');
    const deleteWebhookBtn = document.getElementById('deleteWebhookBtn');
    const webhookStatus = document.getElementById('webhookStatus');

    // Set webhook button
    setWebhookBtn.addEventListener('click', function() {
        setWebhookBtn.disabled = true;
        setWebhookBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Setting webhook...';
        
        fetch('/set_webhook')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    webhookStatus.className = 'alert alert-success';
                    webhookStatus.innerHTML = `
                        <i class="fas fa-check-circle me-2"></i>
                        <strong>Success!</strong> Webhook set successfully.
                        <div class="mt-2">
                            <small class="text-muted">Webhook URL: ${data.message.split(': ')[1]}</small>
                        </div>
                    `;
                } else {
                    // Check if this is an HTTPS error
                    if (data.is_https === false) {
                        webhookStatus.className = 'alert alert-warning';
                        webhookStatus.innerHTML = `
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>HTTPS Required!</strong> ${data.message}
                            <div class="mt-3">
                                <p><strong>Why this happens:</strong> Telegram requires all webhook URLs to use HTTPS for security.</p>
                                <p><strong>Current URL:</strong> <code>${data.webhook_url}</code></p>
                                <p><strong>Solutions:</strong></p>
                                <ul>
                                    <li>Deploy this application to a hosting service that offers HTTPS</li>
                                    <li>Use a tunnel service like ngrok to expose your local server via HTTPS</li>
                                    <li>For testing only: Use Telegram's getUpdates polling method instead of webhooks</li>
                                </ul>
                            </div>
                        `;
                    } else {
                        webhookStatus.className = 'alert alert-danger';
                        webhookStatus.innerHTML = `
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>Error!</strong> ${data.message}
                        `;
                    }
                }
            })
            .catch(error => {
                webhookStatus.className = 'alert alert-danger';
                webhookStatus.innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Error!</strong> ${error.message}
                `;
            })
            .finally(() => {
                setWebhookBtn.disabled = false;
                setWebhookBtn.innerHTML = '<i class="fas fa-link me-2"></i>Set Webhook';
            });
    });

    // Get webhook info button
    getWebhookInfoBtn.addEventListener('click', function() {
        getWebhookInfoBtn.disabled = true;
        getWebhookInfoBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Getting info...';
        
        fetch('/webhook_info')
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    const webhookInfo = data.webhook_info.result;
                    
                    if (webhookInfo.url) {
                        webhookStatus.className = 'alert alert-info';
                        webhookStatus.innerHTML = `
                            <h5><i class="fas fa-info-circle me-2"></i>Webhook Information</h5>
                            <ul class="list-group mt-3">
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>URL</span>
                                    <code>${webhookInfo.url}</code>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>Has Custom Certificate</span>
                                    <span>${webhookInfo.has_custom_certificate ? 'Yes' : 'No'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>Pending Update Count</span>
                                    <span>${webhookInfo.pending_update_count}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>Last Error Date</span>
                                    <span>${webhookInfo.last_error_date ? new Date(webhookInfo.last_error_date * 1000).toLocaleString() : 'None'}</span>
                                </li>
                                <li class="list-group-item d-flex justify-content-between align-items-center">
                                    <span>Last Error Message</span>
                                    <span>${webhookInfo.last_error_message || 'None'}</span>
                                </li>
                            </ul>
                        `;
                    } else {
                        webhookStatus.className = 'alert alert-warning';
                        webhookStatus.innerHTML = `
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>No webhook set!</strong> Use the "Set Webhook" button to configure a webhook.
                        `;
                    }
                } else {
                    webhookStatus.className = 'alert alert-danger';
                    webhookStatus.innerHTML = `
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>Error!</strong> ${data.message}
                    `;
                }
            })
            .catch(error => {
                webhookStatus.className = 'alert alert-danger';
                webhookStatus.innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Error!</strong> ${error.message}
                `;
            })
            .finally(() => {
                getWebhookInfoBtn.disabled = false;
                getWebhookInfoBtn.innerHTML = '<i class="fas fa-info-circle me-2"></i>Get Webhook Info';
            });
    });

    // Delete webhook button
    deleteWebhookBtn.addEventListener('click', function() {
        if (confirm('Are you sure you want to delete the webhook?')) {
            deleteWebhookBtn.disabled = true;
            deleteWebhookBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Deleting...';
            
            fetch('/delete_webhook')
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'success') {
                        webhookStatus.className = 'alert alert-success';
                        webhookStatus.innerHTML = `
                            <i class="fas fa-check-circle me-2"></i>
                            <strong>Success!</strong> Webhook deleted successfully.
                        `;
                    } else {
                        webhookStatus.className = 'alert alert-danger';
                        webhookStatus.innerHTML = `
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>Error!</strong> ${data.message}
                        `;
                    }
                })
                .catch(error => {
                    webhookStatus.className = 'alert alert-danger';
                    webhookStatus.innerHTML = `
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        <strong>Error!</strong> ${error.message}
                    `;
                })
                .finally(() => {
                    deleteWebhookBtn.disabled = false;
                    deleteWebhookBtn.innerHTML = '<i class="fas fa-unlink me-2"></i>Delete Webhook';
                });
        }
    });

    // Test message type selector
    const testMessage = document.getElementById('testMessage');
    const customMessageContainer = document.getElementById('customMessageContainer');
    const customMessage = document.getElementById('customMessage');
    const testBotForm = document.getElementById('testBotForm');
    const testChatId = document.getElementById('testChatId');
    const sendTestBtn = document.getElementById('sendTestBtn');
    const testResult = document.getElementById('testResult');
    const testResponse = document.getElementById('testResponse');
    
    // Show/hide custom message textarea based on selection
    testMessage.addEventListener('change', function() {
        if (testMessage.value === 'custom') {
            customMessageContainer.style.display = 'block';
        } else {
            customMessageContainer.style.display = 'none';
        }
    });
    
    // Handle test bot form submission
    testBotForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get values
        const chatId = testChatId.value.trim() || '123456789'; // Default test ID if not provided
        let messageText = testMessage.value;
        
        if (messageText === 'custom') {
            messageText = customMessage.value.trim();
            if (!messageText) {
                alert('Please enter a custom message');
                return;
            }
        }
        
        // Disable send button
        sendTestBtn.disabled = true;
        sendTestBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Sending...';
        
        // Simulate processing the command or message
        const testData = {
            chat_id: chatId,
            message: messageText,
            date: new Date().toISOString()
        };
        
        // Make the API call to test the command
        fetch('/test_bot', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(testData)
        })
        .then(response => response.json())
        .then(data => {
            // Display the result
            testResult.style.display = 'block';
            
            if (data.status === 'success') {
                testResponse.className = 'alert alert-success';
                
                let responseHtml = `
                    <h6><i class="fas fa-check-circle me-2"></i>Message processed successfully</h6>
                    <hr>
                    <div class="card bg-dark">
                        <div class="card-header">
                            <strong>Bot Response:</strong>
                        </div>
                        <div class="card-body">
                            <pre class="mb-0">${data.response ? data.response.text || JSON.stringify(data.response, null, 2) : 'No response content'}</pre>
                        </div>
                    </div>
                `;
                
                testResponse.innerHTML = responseHtml;
            } else {
                testResponse.className = 'alert alert-danger';
                testResponse.innerHTML = `
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    <strong>Error:</strong> ${data.message || 'Unknown error occurred'}
                `;
            }
        })
        .catch(error => {
            testResult.style.display = 'block';
            testResponse.className = 'alert alert-danger';
            testResponse.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Error:</strong> ${error.message}
            `;
        })
        .finally(() => {
            // Re-enable send button
            sendTestBtn.disabled = false;
            sendTestBtn.innerHTML = '<i class="fas fa-paper-plane me-2"></i>Send Test Message';
        });
    });
    
    // Check webhook status on page load
    getWebhookInfoBtn.click();
});
