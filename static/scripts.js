setInterval(function () {
    fetch("http://localhost:8000/logs")
        .then(function (response) {
            return response.json();
        }).then(function (logs) {
            var logsElements = document.getElementById("logs");
            while (logsElements.firstChild) {
                logsElements.removeChild(logsElements.lastChild);
            }

            for (var log of logs) {
                var item = document.createElement("li")
                item.innerHTML = `
                    <div class="flex border-b p-2">
                        <div class="flex-1 flex flex-col">
                            <div class="font-medium">${log.system}</div>
                            <div>${log.value}</div>
                        </div>
                        <div class="flex-1">${log.explanation}</div>
                    </div>`;
                logsElements.insertAdjacentElement('afterbegin', item);
            }
        }).catch(function (err) {
            console.error(err);
        });
}, 2000)


setInterval(function () {
    fetch("http://localhost:8000/state")
        .then(function (response) {
            return response.json();
        }).then(function (data) {
            document.getElementById("thermostat").innerText = data.thermostat;
            document.getElementById("shutter").innerText = data.shutter;
            document.getElementById("music").innerText = data.music;
        }).catch(function (err) {
            console.error(err)
        })
}, 2000)


function send_request(event) {
    event.preventDefault();

    const input = document.getElementById("request").value;

    fetch(`http://localhost:8000/input`, { method: "POST", headers: { 'content-type': 'application/json' }, body: JSON.stringify({ request: input }) }).then(function () {
        console.log('sent')
    }).catch(function (err) {
        console.error(err)
    })
}