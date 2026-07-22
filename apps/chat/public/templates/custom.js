
document.addEventListener('DOMContentLoaded', () => {
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === 1) { // Element node
                    // Check if the node itself is a message or contains messages
                    const messages = node.querySelectorAll ? node.querySelectorAll('.message-content') : [];
                    
                    // Also check the node itself if it has the class
                    if (node.classList && node.classList.contains('message-content')) {
                        checkAndRemove(node);
                    }

                    messages.forEach(checkAndRemove);
                }
            });
        });
    });

    const targetNode = document.body;
    const config = { childList: true, subtree: true };
    observer.observe(targetNode, config);

    function checkAndRemove(element) {
        console.log(element.textContent);

        if (element.textContent.includes("🤓 I noticed a small mistake. Here is the corrected version:")) {
            setTimeout(() => {
                // Find the parent container that represents the whole message bubble to remove it cleanly
                // This might need adjustment based on the exact DOM structure of Chainlit
                const messageContainer = element.closest('.message-row') || element.closest('.step'); 
                if (messageContainer) {
                    messageContainer.style.transition = "opacity 1s ease-out";
                    messageContainer.style.opacity = "0";
                    setTimeout(() => {
                        messageContainer.remove();
                    }, 1000);
                } else {
                    // Fallback if container not found
                    element.style.transition = "opacity 1s ease-out";
                    element.style.opacity = "0";
                     setTimeout(() => {
                        element.remove();
                    }, 1000);
                }
            }, 10000); // 30 seconds
        }
    }
});
