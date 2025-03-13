

window.showToast = function (message, type = "info") {
  const toastContainer = document.getElementById("toast-container");
  if (!toastContainer) return;

  toastContainer.style.display = "flex";

  const toast = document.createElement("div");
  toast.className =
    "toast flex items-center p-4 mb-3 rounded-lg shadow-md transition transform duration-300 ease-in-out";

  let iconClass = "";
  switch (type) {
    case "success":
      toast.classList.add(
        "bg-green-50",
        "border-l-4",
        "border-green-500",
        "text-green-700"
      );
      iconClass = "fas fa-check-circle text-green-500";
      break;
    case "error":
      toast.classList.add(
        "bg-red-50",
        "border-l-4",
        "border-red-500",
        "text-red-700"
      );
      iconClass = "fas fa-exclamation-circle text-red-500";
      break;
    case "warning":
      toast.classList.add(
        "bg-yellow-50",
        "border-l-4",
        "border-yellow-500",
        "text-yellow-700"
      );
      iconClass = "fas fa-exclamation-triangle text-yellow-500";
      break;
    default: 
      toast.classList.add(
        "bg-blue-50",
        "border-l-4",
        "border-blue-500",
        "text-blue-700"
      );
      iconClass = "fas fa-info-circle text-blue-500";
  }

  toast.innerHTML = `
    <div class="flex">
      <div class="flex-shrink-0 mr-3">
        <i class="${iconClass} text-lg"></i>
      </div>
      <div class="flex-grow">
        ${message}
      </div>
      <div class="flex-shrink-0 ml-3">
        <button type="button" class="toast-close">
          <i class="fas fa-times text-gray-400 hover:text-gray-600"></i>
        </button>
      </div>
    </div>
  `;

  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.classList.add("translate-y-0", "opacity-100");
  }, 10);

  const closeButton = toast.querySelector(".toast-close");
  closeButton.addEventListener("click", () => {
    removeToast(toast);
  });

  setTimeout(() => {
    removeToast(toast);
  }, 5000);

  function removeToast(toastElement) {
    toastElement.classList.add("opacity-0", "-translate-y-2");
    setTimeout(() => {
      toastElement.remove();
      if (toastContainer.children.length === 0) {
        toastContainer.style.display = "none";
      }
    }, 300);
  }
};


document.addEventListener("DOMContentLoaded", function () {
  const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
  const commentContainer =
    document.getElementById("comments-container") || document;
  const mainContainer = document.body;

  commentContainer.addEventListener("click", function (e) {
    const target = e.target.closest("button, a");
    if (!target) return;

    if (target.classList.contains("reply-button")) {
      handleReplyClick(e, target);
    } else if (target.classList.contains("show-replies-button")) {
      handleShowReplies(e, target);
    } else if (target.classList.contains("like-comment-button")) {
      handleCommentLike(e, target);
    } else if (target.classList.contains("cancel-reply-button")) {
      const replyContainer = target.closest(".reply-form-container");
      if (replyContainer) replyContainer.remove();
    }
  });

  mainContainer.addEventListener("click", function (e) {
    const target = e.target.closest("button, a");
    if (!target) return;

    if (target.classList.contains("like-post-button")) {
      handlePostLike(e, target);
    } else if (target.classList.contains("follow-button")) {
      handleFollowUser(e, target);
    }
  });

  commentContainer.addEventListener("submit", function (e) {
    const form = e.target;
    if (form.classList.contains("reply-form")) {
      handleReplySubmit(e, form);
    }
  });

  function handleReplyClick(e, button) {
    e.preventDefault();

    if (!csrfToken) {
      window.location.href = "/login/";
      return;
    }

    const commentId = button.dataset.commentId;
    const commentAuthor = button.dataset.commentAuthor;
    const authorId = button.dataset.authorId;

    let replyContainer = document.querySelector(
      `.reply-form-container[data-comment-id="${commentId}"]`
    );

    if (replyContainer) {
      replyContainer.remove();
      return;
    }

    const commentElement = button.closest(".comment");
    if (!commentElement) return;

    replyContainer = document.createElement("div");
    replyContainer.className = "reply-form-container mt-3 ml-10";
    replyContainer.dataset.commentId = commentId;

    replyContainer.innerHTML = `
      <form class="reply-form flex space-x-2" action="/comment/${commentId}/reply/" method="post">
        <input type="hidden" name="csrfmiddlewaretoken" value="${csrfToken}">
        <input type="hidden" name="replied_to_id" value="${authorId}">
        <div class="flex-1 relative">
          <textarea name="content" rows="1" 
            class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:ring-purple-500 focus:border-purple-500 sm:text-sm" 
            placeholder="Reply to @${commentAuthor}..." required></textarea>
          <div class="flex justify-end mt-2 space-x-2">
            <button type="button" class="cancel-reply-button px-3 py-1 text-sm border border-gray-300 rounded-md hover:bg-gray-100">
              Cancel
            </button>
            <button type="submit" class="px-3 py-1 text-sm bg-purple-600 text-white rounded-md hover:bg-purple-700">
              Reply
            </button>
          </div>
        </div>
      </form>
    `;

    const actionsDiv =
      commentElement.querySelector(".comment-actions") || commentElement;
    actionsDiv.parentNode.insertBefore(replyContainer, actionsDiv.nextSibling);

    setTimeout(() => {
      replyContainer.querySelector('textarea[name="content"]').focus();
    }, 0);
  }

  function handleReplySubmit(e, form) {
    e.preventDefault();

    const url = form.getAttribute("action");
    const commentId = url.match(/\/comment\/(\d+)\/reply\//)?.[1];

    if (!commentId) {
      console.error("Invalid comment ID");
      return;
    }

    const submitButton = form.querySelector('button[type="submit"]');
    const originalText = submitButton.innerHTML;
    submitButton.innerHTML =
      '<i class="fas fa-spinner fa-spin mr-1.5"></i> Sending...';
    submitButton.disabled = true;

    const formData = new FormData(form);

    fetch(url, {
      method: "POST",
      body: formData,
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrfToken,
      },
      credentials: "same-origin",
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.status === "success") {
          let repliesContainer = document.querySelector(
            `.replies-container[data-comment-id="${commentId}"]`
          );

          if (!repliesContainer) {
            const commentElement = form.closest(".comment");
            if (!commentElement) return;

            repliesContainer = document.createElement("div");
            repliesContainer.className =
              "replies-container ml-10 mt-3 space-y-3";
            repliesContainer.dataset.commentId = commentId;
            repliesContainer.dataset.loaded = "true";
            commentElement.appendChild(repliesContainer);
          }

          const replyHTML = createReplyHTML(data);
          repliesContainer.insertAdjacentHTML("beforeend", replyHTML);
          repliesContainer.classList.remove("hidden");

          const newReply = repliesContainer.querySelector(
            `#comment-${data.comment_id}`
          );
          if (newReply) {
            const likeButton = newReply.querySelector(".like-comment-button");
            if (likeButton) {
              likeButton.dataset.authenticated = "true";
              likeButton.dataset.liked = "false";
            }
          }

          updateRepliesCounter(commentId);

          const replyContainer = form.closest(".reply-form-container");
          if (replyContainer) {
            replyContainer.remove();
          }

          if (window.showToast) {
            window.showToast("Reply added successfully", "success");
          }
        } else {
          submitButton.innerHTML = originalText;
          submitButton.disabled = false;

          if (window.showToast) {
            window.showToast(data.error || "Error sending reply", "error");
          }
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        submitButton.innerHTML = originalText;
        submitButton.disabled = false;

        if (window.showToast) {
          window.showToast("An error occurred while sending reply", "error");
        }
      });
  }

  function handleShowReplies(e, button) {
    e.preventDefault();

    const commentId = button.dataset.commentId;
    let repliesContainer = document.querySelector(
      `.replies-container[data-comment-id="${commentId}"]`
    );

    if (!repliesContainer) {
      const commentElement = button.closest(".comment");
      if (!commentElement) return;

      repliesContainer = document.createElement("div");
      repliesContainer.className = "replies-container ml-10 mt-3 space-y-3";
      repliesContainer.dataset.commentId = commentId;
      commentElement.appendChild(repliesContainer);

      loadReplies(commentId, repliesContainer, button);
    } else if (repliesContainer.dataset.loaded === "true") {
      const isHidden = repliesContainer.classList.toggle("hidden");
      button.innerHTML = isHidden
        ? `<i class="fas fa-reply-all mr-1"></i> Show replies (${
            button.dataset.repliesCount || 0
          })`
        : '<i class="fas fa-minus mr-1"></i> Hide replies';
    } else {
      loadReplies(commentId, repliesContainer, button);
    }
  }

  function loadReplies(commentId, container, button) {
    button.innerHTML = '<i class="fas fa-spinner fa-spin mr-1"></i> Loading...';
    button.disabled = true;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10000);

    fetch(`/comment/${commentId}/get_replies/`, {
      method: "POST",
      headers: {
        "X-Requested-With": "XMLHttpRequest",
        "X-CSRFToken": csrfToken,
        "Content-Type": "application/json",
      },
      signal: controller.signal,
      credentials: "same-origin",
    })
      .then((response) => {
        clearTimeout(timeoutId);
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.status === "success") {
          container.innerHTML = "";

          if (data.replies.length === 0) {
            container.innerHTML =
              '<div class="text-gray-500 text-sm py-2">No replies yet</div>';
            button.innerHTML =
              '<i class="fas fa-reply-all mr-1"></i> Replies (0)';
          } else {
            const fragment = document.createDocumentFragment();
            const tempDiv = document.createElement("div");

            data.replies.forEach((reply) => {
              tempDiv.innerHTML = createReplyHTML(reply);
              while (tempDiv.firstChild) {
                fragment.appendChild(tempDiv.firstChild);
              }
            });

            container.appendChild(fragment);
            button.innerHTML = '<i class="fas fa-minus mr-1"></i> Hide replies';
            button.dataset.repliesCount = data.replies.length;
            container.dataset.loaded = "true";
          }
        } else {
          container.innerHTML =
            '<div class="text-red-500 text-sm py-2">Error loading replies</div>';
          button.innerHTML =
            '<i class="fas fa-reply-all mr-1"></i> Show replies';

          if (window.showToast) {
            window.showToast(data.error || "Error loading replies", "error");
          }
        }
        button.disabled = false;
      })
      .catch((error) => {
        clearTimeout(timeoutId);
        console.error("Error:", error);
        container.innerHTML =
          '<div class="text-red-500 text-sm py-2">Error loading replies</div>';
        button.innerHTML = '<i class="fas fa-reply-all mr-1"></i> Show replies';
        button.disabled = false;

        if (window.showToast) {
          window.showToast("An error occurred while loading replies", "error");
        }
      });
  }

  function updateRepliesCounter(commentId) {
    const button = document.querySelector(
      `.show-replies-button[data-comment-id="${commentId}"]`
    );
    const repliesContainer = document.querySelector(
      `.replies-container[data-comment-id="${commentId}"]`
    );

    if (button && repliesContainer) {
      const repliesCount =
        repliesContainer.querySelectorAll(".comment.reply").length;
      button.dataset.repliesCount = repliesCount;

      if (repliesCount > 0) {
        button.classList.remove("hidden");
        button.innerHTML = repliesContainer.classList.contains("hidden")
          ? `<i class="fas fa-reply-all mr-1"></i> Show replies (${repliesCount})`
          : '<i class="fas fa-minus mr-1"></i> Hide replies';
      } else {
        button.classList.add("hidden");
      }
    }
  }

  function handleCommentLike(e, button) {
    e.preventDefault();

    if (!csrfToken) {
      window.location.href = "/login/";
      return;
    }

    if (button.dataset.authenticated !== "true") {
      window.location.href = "/login/";
      return;
    }

    const commentId = button.dataset.commentId;
    const likeIcon = button.querySelector("i");
    const originalClass = likeIcon.className;
    likeIcon.className = "fas fa-spinner fa-spin";
    button.disabled = true;

    fetch(`/comment/${commentId}/like/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify({}),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        likeIcon.className = data.liked
          ? "fas fa-heart text-red-500"
          : "far fa-heart";
        button.dataset.liked = data.liked ? "true" : "false";

        const likeCountEl = button.querySelector(".comment-like-count");
        if (likeCountEl) likeCountEl.textContent = data.likes_count;

        button.disabled = false;
      })
      .catch((error) => {
        console.error("Error:", error);
        likeIcon.className = originalClass;
        button.disabled = false;

        if (window.showToast) {
          window.showToast("Failed to update like status", "error");
        }
      });
  }

function handlePostLike(e, button) {
  e.preventDefault();

  if (!csrfToken) {
    window.location.href = "/login/";
    return;
  }

  const noteId = button.dataset.noteId;
  const likeIcon = button.querySelector("i");

  if (!likeIcon) {
    console.error("Like icon not found in button:", button);
    if (window.showToast) {
      window.showToast("Error updating like status", "error");
    }
    return;
  }

  const originalIconClass = likeIcon.className;

  likeIcon.className = "fas fa-spinner fa-spin";
  if (button.querySelector(".like-count")) {
    button.querySelector(".like-count").style.opacity = "0.5";
  }
  button.disabled = true;

  fetch(`/note/${noteId}/like/`, {
    method: "POST",
    headers: {
      "X-CSRFToken": csrfToken,
      "Content-Type": "application/json",
      "X-Requested-With": "XMLHttpRequest",
    },
    credentials: "same-origin",
    body: JSON.stringify({}),
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      return response.json();
    })
    .then((data) => {
      try {
        const isHomePage = button.closest("article") !== null;

        if (isHomePage) {
          const buttonDiv = button.querySelector("div");

          if (buttonDiv) {
            if (data.liked) {
              buttonDiv.classList.add("text-red-500", "bg-red-50");
            } else {
              buttonDiv.classList.remove("text-red-500", "bg-red-50");
            }
          }

          likeIcon.className = data.liked ? "fas fa-heart" : "far fa-heart";

          const likeCountEl = button.querySelector(".like-count");
          if (likeCountEl) {
            likeCountEl.textContent = data.likes_count;
            likeCountEl.style.opacity = "1";
            if (data.liked) {
              likeCountEl.classList.add("text-red-500");
            } else {
              likeCountEl.classList.remove("text-red-500");
            }
          } else if (data.likes_count > 0) {
            const countSpan = document.createElement("span");
            countSpan.className = `text-sm ml-1 ${
              data.liked ? "text-red-500" : ""
            } group-hover:text-red-500 like-count`;
            countSpan.dataset.noteId = noteId;
            countSpan.textContent = data.likes_count;
            button.appendChild(countSpan);
          }
        } else {
          if (data.liked) {
            button.className =
              "inline-flex items-center px-2.5 py-1.5 border text-xs leading-4 font-medium rounded focus:outline-none transition-colors like-post-button bg-red-50 text-red-700 border-red-300 hover:bg-red-100";
            likeIcon.className = "fas fa-heart text-red-500 mr-1.5";
          } else {
            button.className =
              "inline-flex items-center px-2.5 py-1.5 border text-xs leading-4 font-medium rounded focus:outline-none transition-colors like-post-button text-gray-700 border-gray-300 bg-white hover:bg-gray-50";
            likeIcon.className = "far fa-heart mr-1.5";
          }

          const likeCountEl = button.querySelector(".like-count");
          if (likeCountEl) {
            likeCountEl.textContent = data.likes_count;
            likeCountEl.style.opacity = "1";
          }
        }

        button.dataset.liked = data.liked ? "true" : "false";

        try {
          const likedPosts = JSON.parse(
            localStorage.getItem("likedPosts") || "{}"
          );
          if (data.liked) {
            likedPosts[noteId] = true;
          } else {
            delete likedPosts[noteId];
          }
          localStorage.setItem("likedPosts", JSON.stringify(likedPosts));
        } catch (storageError) {
          console.warn(
            "Could not save like state to localStorage:",
            storageError
          );
        }
      } catch (error) {
        console.error("Error updating UI:", error);

        likeIcon.className = originalIconClass;

        if (window.showToast) {
          window.showToast(
            "UI update failed but your like was processed. Please refresh to see changes.",
            "warning"
          );
        }
      }

      button.disabled = false;
    })
    .catch((error) => {
      console.error("Network or server error:", error);
      likeIcon.className = originalIconClass;
      button.disabled = false;

      if (window.showToast) {
        window.showToast(
          "Failed to update like status. Try again later.",
          "error"
        );
      }
    });
}

document.addEventListener("DOMContentLoaded", function () {
  try {
    const likedPosts = JSON.parse(localStorage.getItem("likedPosts") || "{}");
    const likeButtons = document.querySelectorAll(".like-post-button");

    likeButtons.forEach((button) => {
      const noteId = button.dataset.noteId;
      const isLiked = button.dataset.liked === "true";
      const isHomePage = button.closest("article") !== null;
      const likeIcon = button.querySelector("i");

      if (isLiked) {
        if (isHomePage) {
          const buttonDiv = button.querySelector("div");
          if (buttonDiv) {
            buttonDiv.classList.add("text-red-500", "bg-red-50");
          }

          if (likeIcon) {
            likeIcon.className = "fas fa-heart";
          }

          const likeCountEl = button.querySelector(".like-count");
          if (likeCountEl) {
            likeCountEl.classList.add("text-red-500");
          }
        } else {
          button.className =
            "inline-flex items-center px-2.5 py-1.5 border text-xs leading-4 font-medium rounded focus:outline-none transition-colors like-post-button bg-red-50 text-red-700 border-red-300 hover:bg-red-100";

          if (likeIcon) {
            likeIcon.className = "fas fa-heart text-red-500 mr-1.5";
          }
        }
      } else {
        if (isHomePage) {
          const buttonDiv = button.querySelector("div");
          if (buttonDiv) {
            buttonDiv.classList.remove("text-red-500", "bg-red-50");
          }

          if (likeIcon) {
            likeIcon.className = "far fa-heart";
          }

          const likeCountEl = button.querySelector(".like-count");
          if (likeCountEl) {
            likeCountEl.classList.remove("text-red-500");
          }
        } else {
          button.className =
            "inline-flex items-center px-2.5 py-1.5 border text-xs leading-4 font-medium rounded focus:outline-none transition-colors like-post-button text-gray-700 border-gray-300 bg-white hover:bg-gray-50";

          if (likeIcon) {
            likeIcon.className = "far fa-heart mr-1.5";
          }
        }
      }
    });
  } catch (error) {
    console.error("Error initializing like buttons:", error);
  }
});
  function handleFollowUser(e, button) {
    e.preventDefault();

    if (!csrfToken) {
      window.location.href = "/login/";
      return;
    }

    const username = button.dataset.username;
    const isFollowing = button.dataset.following === "true";
    const originalText = button.innerHTML;

    button.innerHTML =
      '<i class="fas fa-spinner fa-spin mr-1"></i> ' +
      (isFollowing ? "Unfollowing..." : "Following...");
    button.disabled = true;

    fetch(`/profile/${username}/follow/`, {
      method: "POST",
      headers: {
        "X-CSRFToken": csrfToken,
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
      },
      credentials: "same-origin",
      body: JSON.stringify({}),
    })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
      })
      .then((data) => {
        if (data.following) {
          button.innerHTML = '<i class="fas fa-user-minus mr-1"></i> Unfollow';
          button.classList.remove("bg-purple-600", "hover:bg-purple-700");
          button.classList.add("bg-gray-600", "hover:bg-gray-700");
        } else {
          button.innerHTML = '<i class="fas fa-user-plus mr-1"></i> Follow';
          button.classList.remove("bg-gray-600", "hover:bg-gray-700");
          button.classList.add("bg-purple-600", "hover:bg-purple-700");
        }

        button.dataset.following = data.following ? "true" : "false";
        button.disabled = false;

        const followerCountEl = document.querySelector(".follower-count");
        if (followerCountEl) {
          followerCountEl.textContent = data.followers_count;
        }

        if (window.showToast) {
          window.showToast(
            data.following ? "Now following this user" : "Unfollowed this user",
            "success"
          );
        }
      })
      .catch((error) => {
        console.error("Error:", error);
        button.innerHTML = originalText;
        button.disabled = false;

        if (window.showToast) {
          window.showToast("Failed to update follow status", "error");
        }
      });
  }

  const createReplyHTML = (function () {
    const cache = new Map();

    return function (reply) {
      const cacheKey = `${reply.id}-${reply.content}-${reply.likes_count}-${reply.user_likes}`;

      if (cache.has(cacheKey)) {
        return cache.get(cacheKey);
      }

      const repliedToText = reply.replied_to
        ? `<span class="text-purple-600 font-medium">@${escapeHTML(
            reply.replied_to
          )}</span> `
        : "";

      const userAvatar = reply.author_avatar
        ? `<img src="${escapeHTML(reply.author_avatar)}" alt="${escapeHTML(
            reply.author
          )}" class="w-8 h-8 rounded-full object-cover">`
        : `<div class="w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center text-purple-500">
             <i class="fas fa-user text-sm"></i>
           </div>`;

      const userLikes = reply.user_likes ? "text-red-500 fas" : "far";

      const editDeleteButtons =
        reply.can_edit || reply.can_delete
          ? `<div class="relative ml-auto" x-data="{ open: false }">
             <button @click="open = !open" class="text-gray-400 hover:text-gray-500 focus:outline-none text-sm">
               <i class="fas fa-ellipsis-h"></i>
             </button>
             <div x-show="open" x-cloak @click.away="open = false"
                  class="absolute right-0 mt-1 w-40 bg-white rounded-md shadow-lg py-1 z-10 border border-gray-200">
               ${
                 reply.can_edit
                   ? `<a href="/comment/${reply.id}/edit/" class="block px-4 py-2 text-xs text-gray-700 hover:bg-purple-50">
                      <i class="fas fa-edit mr-2"></i> Edit
                    </a>`
                   : ""
               }
               ${
                 reply.can_delete
                   ? `<a href="/comment/${reply.id}/delete/" class="block px-4 py-2 text-xs text-red-600 hover:bg-red-50">
                      <i class="fas fa-trash-alt mr-2"></i> Delete
                    </a>`
                   : ""
               }
             </div>
           </div>`
          : "";

      const html = `
        <div class="comment reply bg-gray-50 rounded-lg p-3 transition hover:bg-gray-100" id="comment-${
          reply.comment_id || reply.id
        }">
          <div class="flex space-x-2">
            <!-- Reply Author Avatar -->
            <div class="flex-shrink-0">
              <a href="/profile/${escapeHTML(reply.author)}/">
                ${userAvatar}
              </a>
            </div>
            
            <!-- Reply Content -->
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-1">
                  <a href="/profile/${escapeHTML(
                    reply.author
                  )}/" class="font-medium text-gray-900 hover:text-purple-700 transition text-sm">
                    ${escapeHTML(reply.author)}
                  </a>
                  <span class="text-gray-400 text-xs">•</span>
                  <time datetime="${
                    reply.created_at
                  }" class="text-xs text-gray-500">
                    ${reply.created_at}
                  </time>
                </div>
                
                ${editDeleteButtons}
              </div>
              
              <div class="mt-1 text-sm text-gray-800">
                ${repliedToText}${escapeHTML(reply.content).replace(
        /\n/g,
        "<br>"
      )}
              </div>
              
              <!-- Reply Actions -->
              <div class="mt-2 flex items-center space-x-3">
                <!-- Like Button -->
                <button class="flex items-center space-x-1 text-xs text-gray-500 hover:text-gray-700 like-comment-button"
                        data-comment-id="${reply.comment_id || reply.id}"
                        data-authenticated="true"
                        data-liked="${reply.user_likes ? "true" : "false"}">
                  <i class="${userLikes} fa-heart"></i>
                  <span class="comment-like-count" data-comment-id="${
                    reply.comment_id || reply.id
                  }">${reply.likes_count}</span>
                </button>
                
                <!-- Reply Button -->
                <button class="flex items-center space-x-1 text-xs text-gray-500 hover:text-gray-700 reply-button"
                        data-comment-id="${reply.parent_id || reply.id}"
                        data-comment-author="${escapeHTML(reply.author)}"
                        data-author-id="${reply.author_id}">
                  <i class="fas fa-reply"></i>
                  <span>Reply</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      `;

      if (cache.size > 100) {
        const keysIterator = cache.keys();
        for (let i = 0; i < 20; i++) {
          cache.delete(keysIterator.next().value);
        }
      }

      cache.set(cacheKey, html);
      return html;
    };
  })();

  function escapeHTML(str) {
    if (!str || typeof str !== "string") return "";

    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  window.handleCommentLike = handleCommentLike;
  window.handlePostLike = handlePostLike;
  window.handleFollowUser = handleFollowUser;
  window.updateRepliesCounter = updateRepliesCounter;
});
