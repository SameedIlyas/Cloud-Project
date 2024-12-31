import React, { useState } from "react";
import ReactPlayer from "react-player";
import {
  Box,
  VStack,
  HStack,
  Button,
  Text,
  IconButton,
  Spinner,
  Divider,
} from "@chakra-ui/react";
import { DeleteIcon, DownloadIcon } from "@chakra-ui/icons";

function VideoCard(props) {
  const [streamUrl, setStreamUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [playing, setPlaying] = useState(false); // Track if the video is playing

  const handleStream = async () => {
    const token = JSON.parse(localStorage.getItem("user")).access_token; // Get the token from localStorage

    try {
      setLoading(true); // Show loading spinner
      const response = await fetch(
        `https://storage-service-v2-935294039360.us-central1.run.app/storage/stream/${props.filename}`,
        {
          headers: {
            Authorization: `Bearer ${token}`, // Pass the Bearer token
          },
        }
      );

      if (response.ok) {
        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        setStreamUrl(url); // Set the blob URL for streaming
      } else {
        alert("Error streaming video.");
      }
    } catch (error) {
      console.error("Streaming error:", error);
      alert("Error streaming video.");
    } finally {
      setLoading(false); // Hide loading spinner
    }
  };

  const handleDownload = () => {
    props.onDownload(props.filename);
  };

  const handleDelete = () => {
    props.onDelete(props.id);
  };

  const togglePlayback = () => {
    if (!streamUrl) {
      handleStream(); // Load the stream URL if not already loaded
    }
    setPlaying(!playing); // Toggle playing state
  };

  const formatSize = (size) => {
    const sizeInMB = size;
    if (sizeInMB > 1) {
      return `${sizeInMB.toFixed(2)} MB`;
    } else {
      return `${(sizeInMB * 1024).toFixed(2)} KB`;
    }
  };

  return (
    <Box
      borderWidth="1px"
      borderRadius="lg"
      overflow="hidden"
      boxShadow="md"
      p="4"
      maxW="360px"
      bg="gray.50"
    >
      <Box
        h="200px"
        w="100%"
        bg="gray.300"
        borderRadius="md"
        overflow="hidden"
        position="relative"
        onClick={togglePlayback}
        cursor="pointer"
      >
        {loading ? (
          <Spinner
            size="lg"
            color="teal.500"
            position="absolute"
            top="50%"
            left="50%"
            transform="translate(-50%, -50%)"
          />
        ) : (
          <ReactPlayer
            url={streamUrl || props.filePath} // Use stream URL if available, otherwise fallback to file path
            playing={playing} // Control playback state
            controls={false}
            width="100%"
            height="100%"
          />
        )}
      </Box>

      <VStack align="start" spacing="2" mt="4">
        <Text fontWeight="bold" fontSize="lg" isTruncated>
          {props.filename}
        </Text>
        <Text color="gray.600" fontSize="sm">
          Size: {formatSize(props.sizeMb)}
        </Text>
        <Divider />
        <HStack justifyContent="space-between" w="100%">
          <Button
            size="sm"
            colorScheme="teal"
            variant="solid"
            onClick={togglePlayback}
          >
            {playing ? "Pause" : "Play"}
          </Button>
          <HStack spacing="2">
            <IconButton
              size="sm"
              colorScheme="blue"
              aria-label="Download"
              icon={<DownloadIcon />}
              onClick={handleDownload}
            />
            <IconButton
              size="sm"
              colorScheme="red"
              aria-label="Delete"
              icon={<DeleteIcon />}
              onClick={handleDelete}
            />
          </HStack>
        </HStack>
      </VStack>
    </Box>
  );
}

export default VideoCard;
