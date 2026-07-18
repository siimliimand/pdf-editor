console.log("Hello from Background!");

chrome.action.onClicked.addListener(() => {
    chrome.tabs.create({ url: "editor.html" });
});
