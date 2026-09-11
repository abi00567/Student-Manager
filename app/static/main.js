document.addEventListener("DOMContentLoaded", () => {
    const deleteButtons = document.querySelectorAll(".delete-btn");

    deleteButtons.forEach((button) => {
        button.addEventListener("click", async () => {
            const studentId = button.dataset.id;

            const confirmed = confirm(
                "Are you sure you want to delete this student?"
            );

            if (!confirmed) {
                return;
            }

            try {
                const response = await fetch(`/delete/${studentId}`, {
                    method: "DELETE"
                });

                const result = await response.json();

                if (result.success) {
                    window.location.reload();
                } else {
                    alert("Failed to delete student.");
                }
            } catch (error) {
                console.error(error);
                alert("Something went wrong.");
            }
        });
    });
});