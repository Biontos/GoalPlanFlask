document.addEventListener("DOMContentLoaded", function () {
    const cards = document.querySelectorAll(".card-item");
    const lists = document.querySelectorAll(".list-group");

    cards.forEach(card => {
        card.draggable = true;
        card.addEventListener("dragstart", dragStart);
    });

    lists.forEach(list => {
        list.addEventListener("dragover", dragOver);
        list.addEventListener("drop", drop);
    });

    function dragStart(event) {
        event.dataTransfer.setData("text/plain", event.target.id);
    }

    function dragOver(event) {
        event.preventDefault();
    }

    function drop(event) {
        event.preventDefault();
        const cardId = event.dataTransfer.getData("text/plain");
        const card = document.getElementById(cardId);
        const targetList = event.currentTarget;

        targetList.appendChild(card);

        fetch(`/move_card/${cardId}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": getCSRFToken()
            },
            body: JSON.stringify({ new_list_id: targetList.dataset.listId })
        });
    }

    function getCSRFToken() {
        return document.querySelector('input[name="csrf_token"]').value;
    }
});
