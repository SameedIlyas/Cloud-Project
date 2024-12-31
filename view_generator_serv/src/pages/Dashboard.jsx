import React, { useState, useEffect } from "react";
import {
  Box,
  Heading,
  Input,
  Button,
  FormControl,
  FormLabel,
  SimpleGrid,
  Text,
  Select,
  Alert,
  AlertIcon,
  Spinner,
  Divider,
  VStack,
} from "@chakra-ui/react";
import VideoCard from "../components/VideoCard"; // Updated to import VideoCard
import axios from "axios"; // Axios for API calls

const Dashboard = (props) => {
  const { setUsedStorage } = props;
  const [selectedFile, setSelectedFile] = useState(null);
  const [videos, setVideos] = useState([]); // Updated to fetch video data
  const [viewType, setViewType] = useState("grid");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false); // Track upload state
  const [storageInfo, setStorageInfo] = useState(null); // For storing user's storage data
  const [progress, setProgress] = useState(0);
  const token = JSON.parse(localStorage.getItem("user")).access_token;

  useEffect(() => {
    const fetchStorageStatus = async () => {
      try {
        const response = await axios.get(
          "https://storage-service-v2-935294039360.us-central1.run.app/storage/status/",
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );
        setUsedStorage(response.data);
        setStorageInfo(response.data);
        setVideos(response.data.files);
      } catch (err) {
        setError("Failed to fetch storage status.");
      }
    };
    fetchStorageStatus();
  }, [token]);

  const handleFileChange = (event) => {
    setSelectedFile(event.target.files[0]);
  };

  const handleUpload = async (event) => {
    event.preventDefault();
    if (selectedFile) {
      setLoading(true);
      const formData = new FormData();
      formData.append("file", selectedFile);

      try {
        const response = await axios.post(
          "https://storage-service-v2-935294039360.us-central1.run.app/storage/upload/",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
              Authorization: `Bearer ${token}`,
            },
          }
        );

        if (response.data.should_alert) {
          setError("Storage limit reached! Please delete some files.");
        } else {
          setVideos((prevVideos) => [
            ...prevVideos,
            response.data.file_metadata,
          ]);
          setStorageInfo((prevStorage) => ({
            ...prevStorage,
            current_usage_mb:
              prevStorage.current_usage_mb +
              response.data.file_metadata.size_mb,
          }));
          setUsedStorage((prevStorage) => ({
            ...prevStorage,
            current_usage_mb:
              prevStorage.current_usage_mb +
              response.data.file_metadata.size_mb,
          }));
        }
      } catch (err) {
        setError("Error uploading file.");
      } finally {
        setLoading(false);
      }
      setSelectedFile(null);
    }
  };

  const handleDelete = async (videoId) => {
    const videoToDelete = videos.find((video) => video._id === videoId);
    try {
      const response = await axios.delete(
        `https://storage-service-v2-935294039360.us-central1.run.app/storage/files/${videoToDelete.filename}`,
        {
          headers: { Authorization: `Bearer ${token}` },
        }
      );

      if (response.data.message === "File deleted successfully") {
        setVideos((prevVideos) =>
          prevVideos.filter((video) => video._id !== videoId)
        );
        setStorageInfo((prevStorage) => ({
          ...prevStorage,
          current_usage_mb:
            prevStorage.current_usage_mb - videoToDelete.size_mb,
        }));
      }
    } catch (err) {
      setError("Error deleting file.");
    }
  };

  const handleDownload = async (filename) => {
    try {
      const response = await axios.get(
        `https://storage-service-v2-935294039360.us-central1.run.app/storage/download/${filename}`,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          responseType: "blob",
          onDownloadProgress: (progressEvent) => {
            const percent = Math.round(
              (progressEvent.loaded * 100) / progressEvent.total
            );
            setProgress(percent);
          },
        }
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute("download", filename);
      document.body.appendChild(link);
      link.click();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      if (error.response && error.response.status === 404) {
        alert("File not found.");
      } else {
        alert("Error downloading file.");
      }
    }
  };

  const renderVideoCards = () => {
    return videos.map((video) => (
      <VideoCard
        key={video._id}
        id={video._id}
        filePath={video.file_path}
        filename={video.filename}
        mimeType={video.mime_type}
        sizeMb={video.size_mb}
        uploadedAt={video.uploaded_at}
        onDelete={handleDelete}
        onDownload={handleDownload}
      />
    ));
  };

  return (
    <Box p={6} bg="gray.100" minH="100vh">
      {error && (
        <Alert status="error" mb={4}>
          <AlertIcon />
          {error}
        </Alert>
      )}

      <Heading as="h1" textAlign="center" mb={6} color="teal.600">
        Video Storage Dashboard
      </Heading>

      <Box bg="white" p={6} borderRadius="md" boxShadow="md" mb={8}>
        <Heading as="h2" size="lg" mb={4} color="gray.700">
          Upload a New Video
        </Heading>
        <VStack spacing={4} align="stretch">
          <FormControl>
            <FormLabel fontSize="sm" color="gray.600">
              Select a Video File
            </FormLabel>
            <Input
              type="file"
              onChange={handleFileChange}
              accept="video/*"
              isDisabled={loading}
              bg="gray.50"
              border="1px solid"
              borderColor="gray.300"
            />
            <Text fontSize="sm" color="gray.500">
              Only video files are supported.
            </Text>
          </FormControl>
          <Button
            colorScheme="teal"
            onClick={handleUpload}
            isLoading={loading}
            isDisabled={!selectedFile || loading}
          >
            Upload Video
          </Button>
        </VStack>
      </Box>

      <Box bg="white" p={6} borderRadius="md" boxShadow="md" mb={8}>
        <Text fontSize="lg" mb={4} color="gray.700">
          Change View Type:
        </Text>
        <Select
          value={viewType}
          onChange={(e) => setViewType(e.target.value)}
          bg="gray.50"
          border="1px solid"
          borderColor="gray.300"
        >
          <option value="grid">Grid</option>
          <option value="list">List</option>
        </Select>
      </Box>

      <Divider mb={6} />

      <SimpleGrid
        columns={viewType === "list" ? 1 : 3}
        spacing={6}
        justifyContent="center"
      >
        {renderVideoCards()}
      </SimpleGrid>
    </Box>
  );
};

export default Dashboard;
